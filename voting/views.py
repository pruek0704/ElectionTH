# voting/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Citizen, Party, Candidate, VoteUsage
from .forms import CitizenLoginForm

# ─── Helper ───────────────────────────────────────────────────────────────────

SESSION_KEY = 'citizen_id'


def get_citizen(request):
    cid = request.session.get(SESSION_KEY)
    if not cid:
        return None
    try:
        return Citizen.objects.get(pk=cid, is_active=True)
    except Citizen.DoesNotExist:
        return None


def citizen_required(view_func):
    """Decorator: ต้อง login ด้วย Citizen ก่อน"""
    def wrapper(request, *args, **kwargs):
        if not get_citizen(request):
            return redirect('citizen_login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ─── Authentication ────────────────────────────────────────────────────────────

def citizen_login(request):
    if get_citizen(request):
        return redirect('citizen_dashboard')

    form = CitizenLoginForm()

    if request.method == 'POST':
        form = CitizenLoginForm(request.POST)
        if form.is_valid():
            citizen = form.authenticate()
            if citizen:
                request.session[SESSION_KEY] = citizen.pk
                request.session.set_expiry(3600)  # 1 ชั่วโมง
                messages.success(request, f'ยินดีต้อนรับ คุณ{citizen.full_name}')
                return redirect('citizen_dashboard')
            else:
                messages.error(request, 'ชื่อ-นามสกุล หรือ เลขบัตรประชาชนไม่ถูกต้อง')

    return render(request, 'voting/citizen_login.html', {'form': form})


def citizen_logout(request):
    request.session.flush()
    return redirect('citizen_login')


# ─── Citizen Dashboard ─────────────────────────────────────────────────────────

@citizen_required
def citizen_dashboard(request):
    citizen = get_citizen(request)
    usages = VoteUsage.objects.filter(citizen=citizen).values_list('vote_type', flat=True)

    context = {
        'citizen': citizen,
        'voted_constituency': 'constituency' in usages,
        'voted_party': 'party' in usages,
    }
    return render(request, 'voting/citizen_dashboard.html', context)


# ─── Voting: ส.ส. เขต ──────────────────────────────────────────────────────────

@citizen_required
def vote_constituency(request):
    citizen = get_citizen(request)

    # เช็คว่าใช้สิทธิ์ไปแล้วหรือยัง
    if VoteUsage.objects.filter(citizen=citizen, vote_type='constituency').exists():
        messages.warning(request, 'คุณได้ใช้สิทธิ์เลือกตั้ง ส.ส. เขตไปแล้ว')
        return redirect('citizen_dashboard')

    candidates = Candidate.objects.filter(
        district=citizen.district, is_active=True
    ).select_related('party')

    return render(request, 'voting/vote_constituency.html', {
        'citizen': citizen,
        'candidates': candidates,
    })


@citizen_required
@require_POST
def submit_constituency_vote(request):
    citizen = get_citizen(request)
    candidate_id = request.POST.get('candidate_id')

    if not candidate_id:
        messages.error(request, 'กรุณาเลือกผู้สมัคร')
        return redirect('vote_constituency')

    try:
        with transaction.atomic():
            # Double-check ก่อนบันทึก (ป้องกัน Race Condition)
            if VoteUsage.objects.filter(
                citizen=citizen, vote_type='constituency'
            ).exists():
                messages.warning(request, 'คุณได้ใช้สิทธิ์ไปแล้ว')
                return redirect('citizen_dashboard')

            candidate = get_object_or_404(
                Candidate, pk=candidate_id, district=citizen.district, is_active=True
            )

            # บันทึกคะแนน (ใช้ F() ป้องกัน Race Condition)
            Candidate.objects.filter(pk=candidate.pk).update(
                vote_count=F('vote_count') + 1
            )

            # บันทึกประวัติการใช้สิทธิ์ (ไม่บันทึกว่าโหวตให้ใคร)
            VoteUsage.objects.create(citizen=citizen, vote_type='constituency')

        messages.success(request, '✅ ลงคะแนนเลือกตั้ง ส.ส. เขตสำเร็จ')

    except Exception as e:
        messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')

    return redirect('citizen_dashboard')


# ─── Voting: พรรคการเมือง ──────────────────────────────────────────────────────

@citizen_required
def vote_party(request):
    citizen = get_citizen(request)

    if VoteUsage.objects.filter(citizen=citizen, vote_type='party').exists():
        messages.warning(request, 'คุณได้ใช้สิทธิ์เลือกตั้งพรรคไปแล้ว')
        return redirect('citizen_dashboard')

    parties = Party.objects.filter(is_active=True)

    return render(request, 'voting/vote_party.html', {
        'citizen': citizen,
        'parties': parties,
    })


@citizen_required
@require_POST
def submit_party_vote(request):
    citizen = get_citizen(request)
    party_id = request.POST.get('party_id')

    if not party_id:
        messages.error(request, 'กรุณาเลือกพรรค')
        return redirect('vote_party')

    try:
        with transaction.atomic():
            if VoteUsage.objects.filter(citizen=citizen, vote_type='party').exists():
                messages.warning(request, 'คุณได้ใช้สิทธิ์ไปแล้ว')
                return redirect('citizen_dashboard')

            party = get_object_or_404(Party, pk=party_id, is_active=True)

            Party.objects.filter(pk=party.pk).update(
                vote_count=F('vote_count') + 1
            )

            VoteUsage.objects.create(citizen=citizen, vote_type='party')

        messages.success(request, '✅ ลงคะแนนเลือกตั้งพรรคสำเร็จ')

    except Exception as e:
        messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')

    return redirect('citizen_dashboard')


# ─── Admin Dashboard ────────────────────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    return render(request, 'voting/admin_dashboard.html')


@login_required
def admin_constituency_results(request):
    candidates = Candidate.objects.filter(is_active=True).select_related('party').order_by('-vote_count')
    total_votes = sum(c.vote_count for c in candidates)

    context = {
        'candidates': candidates,
        'total_votes': total_votes,
    }
    return render(request, 'voting/admin_constituency_results.html', context)


@login_required
def admin_party_results(request):
    parties = Party.objects.filter(is_active=True).order_by('-vote_count')
    total_votes = sum(p.vote_count for p in parties)

    context = {
        'parties': parties,
        'total_votes': total_votes,
    }
    return render(request, 'voting/admin_party_results.html', context)


@login_required
def api_results(request):
    """API สำหรับ Auto-refresh ฝั่ง Admin"""
    parties = list(Party.objects.filter(is_active=True).values(
        'name', 'short_name', 'color', 'vote_count'
    ).order_by('-vote_count'))
    candidates = list(Candidate.objects.filter(is_active=True).values(
        'full_name', 'candidate_number', 'district', 'vote_count', 'party__name', 'party__color'
    ).order_by('-vote_count'))
    total_party = sum(p['vote_count'] for p in parties)
    total_candidate = sum(c['vote_count'] for c in candidates)
    return JsonResponse({
        'parties': parties,
        'candidates': candidates,
        'total_party': total_party,
        'total_candidate': total_candidate,
    })