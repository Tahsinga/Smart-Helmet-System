import json
import os
import urllib.request
import urllib.error

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import HelmetDevice, SensorData, Alert, Worker
from .serializers import SensorDataSerializer
from .forms import WorkerUserCreationForm
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_GET
from django.contrib.auth import logout
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

class WorkerLoginView(LoginView):
    template_name = "monitoring/login_worker.html"
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True
    next_page = reverse_lazy('dashboard')

    def form_valid(self, form):
        user = form.get_user()
        if user.is_staff:
            form.add_error(None, "Only worker users may log in here.")
            return self.form_invalid(form)
        return super().form_valid(form)


class AdminLoginView(LoginView):
    template_name = "monitoring/login_admin.html"
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True
    next_page = reverse_lazy('dashboard')

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_staff:
            form.add_error(None, "Only admin users may log in here.")
            return self.form_invalid(form)
        return super().form_valid(form)


@csrf_exempt
@api_view(['POST'])
def receive_sensor_data(request):
    device_id = request.data.get('device_id')
    
    print(f"\n=== SENSOR DATA RECEIVED ===")
    print(f"Device ID: {device_id}")
    print(f"Raw data: {request.data}")

    try:
        helmet = HelmetDevice.objects.get(device_id=device_id)
        print(f"✓ Helmet found: {helmet}")
    except HelmetDevice.DoesNotExist:
        print(f"✗ Helmet NOT found for device_id: {device_id}")
        return Response({"error": "Device not registered"}, status=404)

    data = request.data.copy()
    data['helmet'] = helmet.id
    print(f"Data to serialize: {data}")

    serializer = SensorDataSerializer(data=data)

    if serializer.is_valid():
        sensor_data = serializer.save()
        print(f"✓ Data saved successfully")

        # 🚨 Automatic Alert Detection
        if sensor_data.gas_level > 50:
            Alert.objects.create(
                helmet=helmet,
                alert_type='GAS',
                message='Hazardous gas detected'
            )

        if sensor_data.heart_rate > 120:
            Alert.objects.create(
                helmet=helmet,
                alert_type='HEART',
                message='Abnormal heart rate'
            )

        if sensor_data.fall_detected:
            Alert.objects.create(
                helmet=helmet,
                alert_type='FALL',
                message='Fall detected'
            )

        # Calculate motion magnitude for fatigue detection
        motion_magnitude = (sensor_data.motion_x ** 2 + sensor_data.motion_y ** 2) ** 0.5
        if sensor_data.heart_rate >= 115 and motion_magnitude >= 20:
            Alert.objects.create(
                helmet=helmet,
                alert_type='FATIGUE',
                message='Possible fatigue detected'
            )

        return Response({"status": "Data received", "device_id": device_id})

    print(f"✗ Serializer errors: {serializer.errors}")
    return Response(serializer.errors, status=400)

from django.shortcuts import render
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_GET
from django.utils import timezone


@login_required
def dashboard_view(request):
    """
    Renders the supervisor dashboard page (map + alerts + stats).
    Data is fetched from /api/dashboard/live/ via JS polling.
    """
    assigned_helmet_id = ''
    if not request.user.is_staff:
        worker_profile = getattr(request.user, 'worker_profile', None)
        if worker_profile is not None:
            helmet = HelmetDevice.objects.filter(worker=worker_profile).first()
            assigned_helmet_id = helmet.device_id if helmet else ''

    available_helmets = HelmetDevice.objects.filter(worker__isnull=True) if request.user.is_staff else HelmetDevice.objects.none()
    return render(request, "monitoring/dashboard.html", {
        'is_admin': request.user.is_staff,
        'assigned_helmet_id': assigned_helmet_id,
        'available_helmets': available_helmets,
    })


@login_required
def dashboard_map_view(request):
    return render(request, "monitoring/dashboard_map.html", {
        'is_admin': request.user.is_staff,
    })


@require_GET
@login_required
def dashboard_live(request):
    """
    Returns latest sensor reading for each helmet.
    Real-time monitoring of: heart_rate, gas_level, temperature, motion
    """
    from django.db.models import Subquery, OuterRef

    # Optimized query: Get latest sensor data for all helmets using subquery
    latest_sensor_data = SensorData.objects.filter(
        helmet=OuterRef('pk')
    ).order_by('-timestamp')

    helmets_with_latest = HelmetDevice.objects.annotate(
        latest_heart_rate=Subquery(latest_sensor_data.values('heart_rate')[:1]),
        latest_spo2=Subquery(latest_sensor_data.values('spo2')[:1]),
        latest_gas_level=Subquery(latest_sensor_data.values('gas_level')[:1]),
        latest_temperature=Subquery(latest_sensor_data.values('temperature')[:1]),
        latest_humidity=Subquery(latest_sensor_data.values('humidity')[:1]),
        latest_motion=Subquery(latest_sensor_data.values('motion')[:1]),
        latest_motion_x=Subquery(latest_sensor_data.values('motion_x')[:1]),
        latest_motion_y=Subquery(latest_sensor_data.values('motion_y')[:1]),
        latest_fall_detected=Subquery(latest_sensor_data.values('fall_detected')[:1]),
        latest_latitude=Subquery(latest_sensor_data.values('latitude')[:1]),
        latest_longitude=Subquery(latest_sensor_data.values('longitude')[:1]),
        latest_timestamp=Subquery(latest_sensor_data.values('timestamp')[:1])
    ).filter(
        latest_timestamp__isnull=False  # Only include helmets with sensor data
    )

    if not request.user.is_staff:
        worker_profile = getattr(request.user, 'worker_profile', None)
        if worker_profile is None:
            return JsonResponse({"latest_by_helmet": []})
        helmets_with_latest = helmets_with_latest.filter(worker=worker_profile)

    latest_by_helmet = []
    for helmet in helmets_with_latest:
        motion_value = float(helmet.latest_motion or 0)
        motion_x = float(helmet.latest_motion_x or 0)
        motion_y = float(helmet.latest_motion_y or 0)
        motion_magnitude = (motion_x ** 2 + motion_y ** 2) ** 0.5
        display_motion = motion_value if motion_value != 0 else motion_magnitude
        
        latest_by_helmet.append({
            "device_id": helmet.device_id,
            "battery_level": helmet.battery_level,
            "heart_rate": helmet.latest_heart_rate,
            "spo2": float(helmet.latest_spo2 or 0),
            "gas_level": float(helmet.latest_gas_level or 0),
            "temperature": float(helmet.latest_temperature or 0),
            "humidity": float(helmet.latest_humidity or 0),
            "motion": display_motion,
            "motion_x": motion_x,
            "motion_y": motion_y,
            "fall_detected": bool(helmet.latest_fall_detected),
            "latitude": float(helmet.latest_latitude) if helmet.latest_latitude is not None else None,
            "longitude": float(helmet.latest_longitude) if helmet.latest_longitude is not None else None,
            "timestamp": helmet.latest_timestamp.isoformat() if helmet.latest_timestamp else None,
        })

    return JsonResponse({
        "latest_by_helmet": latest_by_helmet,
    })


@csrf_exempt
@login_required
def dashboard_ai_analyze(request):
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return JsonResponse({"error": "OpenAI API key not configured. Set OPENAI_API_KEY on the server."}, status=500)

    device_id = data.get('device_id')
    if not device_id:
        return JsonResponse({"error": "device_id is required"}, status=400)

    heart_rate = data.get('heart_rate')
    spo2 = data.get('spo2')
    gas_level = data.get('gas_level')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    motion = data.get('motion')
    fall_detected = data.get('fall_detected')
    battery_level = data.get('battery_level')
    timestamp = data.get('timestamp')

    prompt = (
        f"You are a safety AI assistant for an industrial helmet monitoring system. "
        f"Analyze the latest reading for helmet {device_id}. "
        f"The device is considered online if it sent data recently, otherwise do not analyze. "
        f"For acceleration/motion, the stable value is around 5; a lower value can indicate a fall. "
        f"Summarize the current state in a short sentence and recommend any action if needed. "
        f"Use no more than 2 short sentences.\n\n"
        f"Sensor values:\n"
        f"Heart rate: {heart_rate}\n"
        f"SpO₂: {spo2}\n"
        f"Gas level: {gas_level}\n"
        f"Temperature: {temperature}\n"
        f"Humidity: {humidity}\n"
        f"Motion: {motion}\n"
        f"Fall detected: {fall_detected}\n"
        f"Battery: {battery_level}\n"
        f"Timestamp: {timestamp}\n"
        f"If there is a fall or abnormal reading, clearly say so."
    )

    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "temperature": 0.25,
        "max_tokens": 140,
        "messages": [
            {"role": "system", "content": "You are a concise safety assistant."},
            {"role": "user", "content": prompt}
        ]
    }).encode('utf-8')

    request_obj = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request_obj, timeout=20) as resp:
            response_data = json.loads(resp.read().decode('utf-8'))
            analysis = response_data.get('choices', [])[0].get('message', {}).get('content', '') if response_data.get('choices') else ''
            return JsonResponse({"analysis": analysis.strip()})
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode('utf-8') if exc else ''
        return JsonResponse({"error": "OpenAI API request failed", "details": error_body}, status=502)
    except Exception as exc:
        return JsonResponse({"error": "AI analysis failed", "details": str(exc)}, status=500)


@require_GET
@login_required
def dashboard_history(request):
    """
    Returns historical sensor data for a specific helmet.
    Query params:
      - device_id: The helmet device ID to fetch history for
      - limit (default 100): Maximum number of records to return
    """
    device_id = request.GET.get('device_id')
    limit = int(request.GET.get('limit', '100'))
    
    if not device_id:
        return JsonResponse({"error": "device_id parameter required"}, status=400)
    
    try:
        helmet = HelmetDevice.objects.get(device_id=device_id)
    except HelmetDevice.DoesNotExist:
        return JsonResponse({"error": f"Device {device_id} not found"}, status=404)

    if not request.user.is_staff:
        worker_profile = getattr(request.user, 'worker_profile', None)
        if helmet.worker != worker_profile:
            return JsonResponse({"error": "Forbidden"}, status=403)
    
    # Get historical data, ordered by timestamp descending (newest first)
    sensor_records = SensorData.objects.filter(helmet=helmet).order_by('-timestamp')[:limit]
    
    history = []
    for record in sensor_records:
        motion_magnitude = (float(record.motion_x or 0) ** 2 + float(record.motion_y or 0) ** 2) ** 0.5
        history.append({
            "device_id": helmet.device_id,
            "heart_rate": record.heart_rate,
            "spo2": float(record.spo2 or 0),
            "gas_level": float(record.gas_level),
            "temperature": float(record.temperature),
            "humidity": float(record.humidity),
            "motion": motion_magnitude,  # For backward compatibility
            "motion_x": float(record.motion_x or 0),
            "motion_y": float(record.motion_y or 0),
            "fall_detected": record.fall_detected,
            "battery_level": helmet.battery_level,
            "timestamp": record.timestamp.isoformat(),
        })
    
    return JsonResponse({
        "device_id": device_id,
        "history": history,
    })

@csrf_exempt
@api_view(['POST'])
def resolve_alert(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id)
    alert.resolved = True
    alert.save(update_fields=["resolved"])
    return Response({"status": "resolved", "alert_id": alert.id})


def logout_view(request):
    logout(request)
    return redirect('/worker-login/')


@login_required
@user_passes_test(lambda u: u.is_staff)
def create_user_view(request):
    """Admin page to add new worker login users."""
    if request.method == 'POST':
        form = WorkerUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.is_superuser = False
            user.save()

            worker = Worker.objects.create(
                user=user,
                name=form.cleaned_data['worker_name'],
                employee_id=form.cleaned_data['employee_id'],
                department=form.cleaned_data['department'],
            )

            helmet = form.cleaned_data.get('helmet')
            if helmet:
                helmet.worker = worker
                helmet.save(update_fields=['worker'])

            success_message = f"Worker user '{user.username}' created successfully."
            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_message})
            messages.success(request, success_message)
            return redirect('create_user')

        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = WorkerUserCreationForm()

    return render(request, 'monitoring/create_user.html', {'form': form})


@require_GET
@login_required
def workers_list_view(request):
    """
    Page: list of workers/helmets to click into history.
    """
    helmets = HelmetDevice.objects.select_related("worker").all()
    return render(request, "monitoring/workers_list.html", {"helmets": helmets})


@require_GET
@login_required
def worker_history_view(request, device_id):
    """
    Page: charts + latest location for a specific helmet/worker.
    """
    helmet = get_object_or_404(HelmetDevice.objects.select_related("worker"), device_id=device_id)
    if not request.user.is_staff:
        worker_profile = getattr(request.user, 'worker_profile', None)
        if helmet.worker != worker_profile:
            return HttpResponseForbidden("You are not allowed to view this helmet.")
    return render(request, "monitoring/worker_history.html", {"helmet": helmet})


@require_GET
@login_required
def worker_history_data(request, device_id):
    """
    JSON: timeseries for charts.
    Query params:
      - minutes (default 60)
    """
    helmet = get_object_or_404(HelmetDevice, device_id=device_id)
    if not request.user.is_staff:
        worker_profile = getattr(request.user, 'worker_profile', None)
        if helmet.worker != worker_profile:
            return JsonResponse({"error": "Forbidden"}, status=403)
    minutes = int(request.GET.get("minutes", "60"))
    since = timezone.now() - timezone.timedelta(minutes=minutes)

    helmet = get_object_or_404(HelmetDevice, device_id=device_id)

    qs = (SensorData.objects
          .filter(helmet=helmet, timestamp__gte=since)
          .order_by("timestamp"))

    points = [{
        "t": s.timestamp.isoformat(),
        "gas": float(s.gas_level),
        "hr": int(s.heart_rate),
        "spo2": float(s.spo2),
        "motion": float(s.motion),
        "temp": float(s.temperature),
        "lat": float(s.latitude),
        "lng": float(s.longitude),
    } for s in qs]

    latest = qs.order_by("-timestamp").first()
    latest_payload = None
    if latest:
        latest_payload = {
            "t": latest.timestamp.isoformat(),
            "lat": float(latest.latitude),
            "lng": float(latest.longitude),
            "gas": float(latest.gas_level),
            "hr": int(latest.heart_rate),
            "motion": float(latest.motion),
            "temp": float(latest.temperature),
        }

    return JsonResponse({
        "device_id": helmet.device_id,
        "points": points,
        "latest": latest_payload,
    })
