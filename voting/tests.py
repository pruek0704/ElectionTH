from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Party, Candidate, VoteUsage, ElectionConfig

class VotingSystemCompleteTest(TestCase):
    def setUp(self):
        # ข้อมูลพื้นฐาน
        self.config = ElectionConfig.objects.create(is_open=True)
        self.party = Party.objects.create(name="พรรคก้าวหน้า", vote_count=0)
        self.candidate = Candidate.objects.create(
            full_name="นายใจดี", party=self.party, district="เขต 1", 
            candidate_number=1, vote_count=0
        )
        # ประชาชน
        self.citizen = User.objects.create_user(
            username="1234567890123", password="1234567890123",
            first_name="สมชัย", national_id="1234567890123", district="เขต 1"
        )
        # แอดมิน
        self.admin = User.objects.create_user(
            username="admin", password="adminpassword", is_staff=True
        )
        self.client = Client()

    # --- TEST CITIZEN VIEWS ---
    
    def test_citizen_login_logic(self):
        """ทดสอบ Logic การล็อกอินของประชาชน (เช็คทั้งชื่อและเลขบัตร)"""
        # กรณีข้อมูลถูก
        response = self.client.post(reverse('citizen_login'), {
            'full_name': 'สมชัย',
            'national_id': '1234567890123'
        })
        self.assertRedirects(response, reverse('citizen_dashboard'))

    def test_vote_constituency_success(self):
        """ทดสอบโหวต ส.ส. เขต (เช็คคะแนน + การบันทึกสิทธิ์)"""
        self.client.force_login(self.citizen)
        response = self.client.post(reverse('submit_constituency'), {'candidate_id': self.candidate.id})
        
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.vote_count, 1)
        # เช็คว่าบันทึกใน VoteUsage จริงไหม
        self.assertTrue(VoteUsage.objects.filter(citizen=self.citizen, vote_type='constituency').exists())

    def test_prevent_double_vote_constituency(self):
        """ป้องกันการโหวต ส.ส. ซ้ำ (Logic จาก views.py บรรทัดที่ 70)"""
        self.client.force_login(self.citizen)
        # โหวตครั้งแรก
        self.client.post(reverse('submit_constituency'), {'candidate_id': self.candidate.id})
        # พยายามโหวตครั้งที่สอง
        response = self.client.post(reverse('submit_constituency'), {'candidate_id': self.candidate.id})
        
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.vote_count, 1) # ต้องเท่าเดิม

    # --- TEST ADMIN VIEWS & DECORATORS ---

    def test_staff_required_decorator(self):
        """ทดสอบว่าประชาชนเข้าหน้าแอดมินไม่ได้ (เช็ค @staff_required)"""
        self.client.force_login(self.citizen)
        urls = ['admin_dashboard', 'admin_party_results', 'admin_constituency_results']
        for url_name in urls:
            response = self.client.get(reverse(url_name))
            # ต้องโดนดีดไปหน้า admin_login (302)
            self.assertEqual(response.status_code, 302)

    def test_admin_results_view(self):
        """ทดสอบว่าแอดมินดูผลคะแนนได้ถูกต้อง"""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_party_results'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "พรรคก้าวหน้า")

    # --- TEST ELECTION STATUS ---

    def test_public_results_redirect_when_open(self):
        """ถ้าหีบเปิดอยู่ ประชาชนต้องดูผลไม่ได้ (302 Redirect)"""
        self.client.force_login(self.citizen)
        self.config.is_open = True
        self.config.save()
        response = self.client.get(reverse('public_results'))
        self.assertRedirects(response, reverse('citizen_dashboard'))

    def test_public_results_show_when_closed(self):
        """ถ้าหีบปิดแล้ว ประชาชนถึงจะดูผลได้ (200 OK)"""
        self.client.force_login(self.citizen)
        self.config.is_open = False
        self.config.save()
        response = self.client.get(reverse('public_results'))
        self.assertEqual(response.status_code, 200)
        
    def test_vote_party_success(self):
        """ทดสอบลงคะแนนพรรค (Logic จาก views.py บรรทัดที่ 84)"""
        self.client.force_login(self.citizen)
        response = self.client.post(reverse('submit_party'), {'party_id': self.party.id})
        
        self.party.refresh_from_db()
        self.assertEqual(self.party.vote_count, 1)
        self.assertTrue(VoteUsage.objects.filter(citizen=self.citizen, vote_type='party').exists())

    def test_citizen_login_fail(self):
        """ทดสอบการล็อกอินผิด (Logic จาก views.py บรรทัดที่ 30)"""
        response = self.client.post(reverse('citizen_login'), {
            'full_name': 'ชื่อปลอม',
            'national_id': '0000000000000'
        })
        # ต้องไม่ redirect ไป dashboard แต่ต้องกลับมาหน้า login เดิม (200)
        self.assertEqual(response.status_code, 200)
        # เช็คว่ามีข้อความแจ้งเตือน Error
        messages = list(response.context['messages'])
        self.assertTrue(len(messages) > 0)

    def test_login_required_protection(self):
        """ทดสอบ @login_required (เช็คว่าคนไม่ล็อกอินเข้าหน้าโหวตไม่ได้)"""
        urls = ['citizen_dashboard', 'vote_party', 'vote_constituency']
        for url_name in urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302) # ต้องโดนไล่ไปหน้า login

    def test_api_results_format(self):
        """ทดสอบ api_results (Logic จาก views.py บรรทัดที่ 124)"""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('api_results'))
        self.assertEqual(response.status_code, 200)
        # เช็คว่าเป็น JSON และมีข้อมูลพรรคที่สร้างไว้ใน setUp
        data = response.json()
        self.assertIn('parties', data)
        self.assertEqual(data['parties'][0]['name'], "พรรคก้าวหน้า")

    def test_toggle_election_status(self):
        """ทดสอบการสลับเปิด-ปิดหีบ (Logic จาก views.py บรรทัดที่ 137)"""
        self.client.force_login(self.admin)
        # ปัจจุบันเป็น True (จาก setUp)
        self.client.post(reverse('toggle_election'))
        self.config.refresh_from_db()
        self.assertFalse(self.config.is_open)