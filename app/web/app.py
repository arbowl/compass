"""Flask web application for metrics tracker."""

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash
)
from datetime import datetime
from pathlib import Path

from app.config import load_config
from app.data import Database, UserRepository, MetricEntryRepository
from app.metrics.registry import REGISTRY
from app.metrics.implementations import register_all_metrics

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"
config = load_config()
db_path = Path(config.database.path)
db_path.parent.mkdir(parents=True, exist_ok=True)
db = Database(db_path)
db.initialize()
user_repo = UserRepository(db)
entry_repo = MetricEntryRepository(db)
register_all_metrics(db)


@app.route("/")
def index():
    """Landing page - user selection."""
    users = user_repo.get_all()
    return render_template("index.html", users=users)


@app.route("/user/<int:user_id>")
def user_dashboard(user_id):
    """Main dashboard for a user - shows daily entry form."""
    user = user_repo.get_by_id(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("index"))
    enabled_metric_names = user_repo.get_enabled_metrics(user_id)
    if not enabled_metric_names:
        enabled_metric_names = config.metrics.enabled_metrics
        user_repo.initialize_user_metrics(user_id, enabled_metric_names)
    enabled_metrics = REGISTRY.get_enabled(enabled_metric_names)
    today_entries = {}
    for metric in enabled_metrics:
        latest = entry_repo.get_latest_for_metric(user_id, metric.name, limit=1)
        if latest:
            latest_entry = latest[0]
            if latest_entry.timestamp.date() == datetime.now().date():
                today_entries[metric.name] = latest_entry.get_value()
    return render_template(
        "dashboard.html",
        user=user,
        metrics=enabled_metrics,
        today_entries=today_entries
    )


@app.route("/user/<int:user_id>/submit", methods=["POST"])
def submit_entries(user_id):
    """Submit daily metric entries."""
    user = user_repo.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    enabled_metric_names = user_repo.get_enabled_metrics(user_id)
    enabled_metrics = REGISTRY.get_enabled(enabled_metric_names)
    results = []
    timestamp = datetime.now()
    for metric in enabled_metrics:
        field_name = f"metric_{metric.name}"
        if metric.input_schema().input_type == "boolean":
            value = field_name in request.form
        else:
            value = request.form.get(field_name, "").strip()
        if not value and metric.input_schema().input_type != "boolean":
            continue
        try:
            if metric.validate(value):
                entry = metric.record(user_id, value, timestamp=timestamp)
                results.append({
                    "metric": metric.name,
                    "success": True,
                    "value": value
                })
            else:
                results.append({
                    "metric": metric.name,
                    "success": False,
                    "error": "Invalid value"
                })
        except Exception as e:
            results.append({
                "metric": metric.name,
                "success": False,
                "error": str(e)
            })
    success_count = sum(1 for r in results if r["success"])
    if success_count > 0:
        flash(f"Successfully logged {success_count} metric(s)!", "success")
    else:
        flash("No metrics were logged", "warning")
    return redirect(url_for("user_dashboard", user_id=user_id))


@app.route("/user/<int:user_id>/trends")
def user_trends(user_id):
    """View trends and aggregates for a user."""
    user = user_repo.get_by_id(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("index"))
    days = request.args.get("days", 7, type=int)
    enabled_metric_names = user_repo.get_enabled_metrics(user_id)
    enabled_metrics = REGISTRY.get_enabled(enabled_metric_names)
    metric_data = []
    for metric in enabled_metrics:
        try:
            aggregates = metric.get_aggregates(user_id, days)
            trends = metric.get_trends(user_id, days)
            metric_data.append({
                "metric": metric,
                "aggregates": aggregates,
                "trends": trends
            })
        except Exception as e:
            print(f"Error getting data for {metric.name}: {e}")
    return render_template(
        "trends.html",
        user=user,
        metric_data=metric_data,
        days=days
    )


@app.route("/users/new", methods=["GET", "POST"])
def new_user():
    """Create a new user."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Name is required", "error")
            return render_template("new_user.html")
        existing = user_repo.get_by_name(name)
        if existing:
            flash("User already exists", "error")
            return render_template("new_user.html")
        user = user_repo.create(name)
        user_repo.initialize_user_metrics(user.id, config.metrics.enabled_metrics)
        flash(f"Welcome, {user.name}!", "success")
        return redirect(url_for("user_dashboard", user_id=user.id))
    return render_template("new_user.html")


@app.route("/user/<int:user_id>/settings")
def user_settings(user_id):
    """User settings - manage enabled metrics."""
    user = user_repo.get_by_id(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("index"))
    all_metrics = REGISTRY.get_all()
    enabled_metric_names = user_repo.get_enabled_metrics(user_id)
    return render_template(
        "settings.html",
        user=user,
        all_metrics=all_metrics,
        enabled_metric_names=enabled_metric_names
    )


@app.route("/user/<int:user_id>/settings/toggle", methods=["POST"])
def toggle_metric(user_id):
    """Toggle a metric on/off for a user."""
    user = user_repo.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    metric_name = request.form.get("metric_name")
    enabled = request.form.get("enabled") == "true"
    if not metric_name:
        return jsonify({"error": "Metric name required"}), 400
    if not REGISTRY.is_registered(metric_name):
        return jsonify({"error": "Metric not found"}), 404
    user_repo.set_metric_enabled(user_id, metric_name, enabled)
    return jsonify({"success": True})


@app.route("/api/metrics")
def api_metrics():
    """API endpoint to get available metrics."""
    all_metrics = REGISTRY.get_all()
    return jsonify({
        "metrics": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "input_schema": m.input_schema().model_dump()
            }
            for m in all_metrics
        ]
    })


if __name__ == "__main__":
    app.run(
        host=config.web.host,
        port=config.web.port,
        debug=config.web.debug
    )
