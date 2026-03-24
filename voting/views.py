# voting/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Party, Candidate, VoteUsage


# ─── Citizen Auth ──────────────────────────────────────────────────────────────

def citizen_login(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('citizen_dashboard')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        national_id = request.POST.get('national_id', '').strip()

        # username ของ Citizen = national_id
        user = authenticate(request, username=national_id, password=national_id)

        if user and not user.is_staff and user.get_full_name() == full_name:
            login(request, user)
            return redirect('citizen_dashboard')
        else:
            messages.error(request, 'ชื่อ-นามสกุล หรือ เลขบัตรประชาชนไม่ถูกต้อง')

    return render(request, 'voting/citizen_login.html')


def citizen_logout(request):
    logout(request)
    return redirect('citizen_login')


# ─── Citizen Views ──────────────────────────────────────────────────────────────

@login_required(login_url='citizen_login')
def citizen_dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    usages = VoteUsage.objects.filter(
        citizen=request.user
    ).values_list('vote_type', flat=True)

    return render(request, 'voting/citizen_dashboard.html', {
        'voted_constituency': 'constituency' in usages,
        'voted_party': 'party' in usages,
    })


@login_required(login_url='citizen_login')
def vote_constituency(request):
    if VoteUsage.objects.filter(citizen=request.user, vote_type='constituency').exists():
        messages.warning(request, 'คุณได้ใช้สิทธิ์ ส.ส. เขตไปแล้ว')
        return redirect('citizen_dashboard')

    candidates = Candidate.objects.filter(
        district=request.user.district, is_active=True
    ).select_related('party') if hasattr(Candidate, 'is_active') else \
    Candidate.objects.filter(district=request.user.district).select_related('party')

    return render(request, 'voting/vote_constituency.html', {'candidates': candidates})


@login_required(login_url='citizen_login')
@require_POST
def submit_constituency_vote(request):
    candidate_id = request.POST.get('candidate_id')
    if not candidate_id:
        messages.error(request, 'กรุณาเลือกผู้สมัคร')
        return redirect('vote_constituency')

    try:
        with transaction.atomic():
            if VoteUsage.objects.filter(citizen=request.user, vote_type='constituency').exists():
                messages.warning(request, 'คุณได้ใช้สิทธิ์ไปแล้ว')
                return redirect('citizen_dashboard')

            candidate = get_object_or_404(Candidate, pk=candidate_id)
            Candidate.objects.filter(pk=candidate.pk).update(vote_count=F('vote_count') + 1)
            VoteUsage.objects.create(citizen=request.user, vote_type='constituency')

        messages.success(request, '✅ ลงคะแนน ส.ส. เขตสำเร็จ')
    except Exception as e:
        messages.error(request, f'เกิดข้อผิดพลาด: {e}')

    return redirect('citizen_dashboard')


@login_required(login_url='citizen_login')
def vote_party(request):
    if VoteUsage.objects.filter(citizen=request.user, vote_type='party').exists():
        messages.warning(request, 'คุณได้ใช้สิทธิ์เลือกพรรคไปแล้ว')
        return redirect('citizen_dashboard')

    parties = Party.objects.all()
    return render(request, 'voting/vote_party.html', {'parties': parties})


@login_required(login_url='citizen_login')
@require_POST
def submit_party_vote(request):
    party_id = request.POST.get('party_id')
    if not party_id:
        messages.error(request, 'กรุณาเลือกพรรค')
        return redirect('vote_party')

    try:
        with transaction.atomic():
            if VoteUsage.objects.filter(citizen=request.user, vote_type='party').exists():
                messages.warning(request, 'คุณได้ใช้สิทธิ์ไปแล้ว')
                return redirect('citizen_dashboard')

            party = get_object_or_404(Party, pk=party_id)
            Party.objects.filter(pk=party.pk).update(vote_count=F('vote_count') + 1)
            VoteUsage.objects.create(citizen=request.user, vote_type='party')

        messages.success(request, '✅ ลงคะแนนพรรคสำเร็จ')
    except Exception as e:
        messages.error(request, f'เกิดข้อผิดพลาด: {e}')

    return redirect('citizen_dashboard')


# ─── Admin Views ────────────────────────────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Username หรือ Password ไม่ถูกต้อง')

    return render(request, 'voting/admin_login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@staff_required
def admin_dashboard(request):
    return render(request, 'voting/admin_dashboard.html')


@staff_required
def admin_constituency_results(request):
    candidates  = Candidate.objects.select_related('party').order_by('-vote_count')
    total_votes = sum(c.vote_count for c in candidates)
    return render(request, 'voting/admin_constituency_results.html', {
        'candidates': candidates,
        'total_votes': total_votes,
    })


@staff_required
def admin_party_results(request):
    parties     = Party.objects.order_by('-vote_count')
    total_votes = sum(p.vote_count for p in parties)
    return render(request, 'voting/admin_party_results.html', {
        'parties': parties,
        'total_votes': total_votes,
    })


@staff_required
def api_results(request):
    parties    = list(Party.objects.values('name', 'short_name', 'color', 'vote_count').order_by('-vote_count'))
    candidates = list(Candidate.objects.values(
        'full_name', 'candidate_number', 'district', 'vote_count', 'party__name', 'party__color'
    ).order_by('-vote_count'))
    return JsonResponse({
        'parties':          parties,
        'candidates':       candidates,
        'total_party':      sum(p['vote_count'] for p in parties),
        'total_candidate':  sum(c['vote_count'] for c in candidates),
    })