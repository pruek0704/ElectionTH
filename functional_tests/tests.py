from selenium import webdriver
from selenium.webdriver.common.by import By
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from voting.models import User, Party, Candidate, ElectionConfig
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class EndToEndElectionTest(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(5) 
        
        # 1. จำลองข้อมูลระบบ
        ElectionConfig.objects.create(is_open=True)
        
        self.party = Party.objects.create(name="พรรคก้าวหน้า", color="#ff0000")
        self.candidate = Candidate.objects.create(
            full_name="นายใจดี สู้ศึก", party=self.party, district="เขต 1", candidate_number=1
        )
        
        # 2. จำลองประชาชน
        User.objects.create_user(
            username="1234567890123", 
            password="1234567890123",
            first_name="สมชัย", 
            national_id="1234567890123",
            district="เขต 1" 
        )
        
        # 3. จำลองแอดมิน (สร้างและเข้ารหัสผ่านให้เป๊ะ)
        admin_user = User(
            username='admin', 
            email='admin@test.com', 
            first_name='Admin',
            national_id='0000000000000',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        admin_user.set_password('adminpassword') 
        admin_user.save() 

    def tearDown(self):
        self.browser.quit()

    def test_full_election_lifecycle(self):
        wait = WebDriverWait(self.browser, 10) 
        
        # ==========================================================
        # PART 1: สมชัยล็อกอินและโหวต
        # ==========================================================
        self.browser.get(self.live_server_url + '/login/')
        wait.until(EC.presence_of_element_located((By.NAME, 'full_name')))
        
        self.browser.execute_script("document.getElementsByName('full_name')[0].value = 'สมชัย';")
        self.browser.execute_script("document.getElementsByName('national_id')[0].value = '1234567890123';")
        self.browser.execute_script("document.forms[0].submit();")
        
        wait.until(EC.url_contains('dashboard'))

        # โหวตพรรค
        self.browser.get(self.live_server_url + '/vote/party/')
        party_radio = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"input[name='party_id'][value='{self.party.id}']")))
        self.browser.execute_script("arguments[0].click();", party_radio)
        self.browser.execute_script("document.forms[0].submit();")
        
        # โหวต ส.ส.
        self.browser.get(self.live_server_url + '/vote/constituency/')
        candidate_radio = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"input[name='candidate_id'][value='{self.candidate.id}']")))
        self.browser.execute_script("arguments[0].click();", candidate_radio)
        self.browser.execute_script("document.forms[0].submit();")

        # เช็คหน้าผลลัพธ์
        self.browser.get(self.live_server_url + '/results/')
        page_text = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body'))).text
        self.assertIn('ยังไม่สามารถดูผลได้', page_text)

        # ล็อกเอาท์
        self.browser.get(self.live_server_url + '/logout/')
        wait.until(EC.url_contains('login'))


        # ==========================================================
        # PART 2: แอดมินล็อกอิน
        # ==========================================================
        self.browser.delete_all_cookies() 
        self.browser.get(self.live_server_url + '/admin-panel/login/')
        wait.until(EC.presence_of_element_located((By.NAME, 'username')))
        
        self.browser.execute_script("document.getElementById('username').value = 'admin';")
        self.browser.execute_script("document.getElementById('password').value = 'adminpassword';")
        self.browser.execute_script("document.forms[0].submit();")
        
        wait.until(lambda driver: 'login' not in driver.current_url)

        # ดูผลคะแนน
        self.browser.get(self.live_server_url + '/admin-panel/party/')
        party_page_text = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body'))).text
        self.assertIn('พรรคก้าวหน้า', party_page_text)
        self.assertIn('1', party_page_text)

        self.browser.get(self.live_server_url + '/admin-panel/constituency/')
        constituency_page_text = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body'))).text
        self.assertIn('นายใจดี สู้ศึก', constituency_page_text)
        self.assertIn('1', constituency_page_text)

        # ปิดหีบเลือกตั้ง
        self.browser.get(self.live_server_url + '/admin-panel/')
        form_toggle = wait.until(EC.presence_of_element_located((By.XPATH, "//form[@action='/admin-panel/toggle/']")))
        self.browser.execute_script("arguments[0].submit();", form_toggle) # บังคับ Submit ให้ข้าม Popup แจ้งเตือนไปเลย
        time.sleep(1.5) 
        
        # รีเฟรชหน้าเพื่อเช็คว่าเปลี่ยนสถานะเป็น "ปิด" แล้วจริงๆ
        self.browser.get(self.live_server_url + '/admin-panel/')
        admin_dashboard_text = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body'))).text
        self.assertIn('ปิด', admin_dashboard_text) 

        self.browser.get(self.live_server_url + '/admin-panel/logout/')
        wait.until(EC.url_contains('login'))


        # ==========================================================
        # PART 3: สมชัยกลับมาดูผล
        # ==========================================================
        self.browser.get(self.live_server_url + '/login/')
        wait.until(EC.presence_of_element_located((By.NAME, 'full_name')))
        
        self.browser.execute_script("document.getElementsByName('full_name')[0].value = 'สมชัย';")
        self.browser.execute_script("document.getElementsByName('national_id')[0].value = '1234567890123';")
        self.browser.execute_script("document.forms[0].submit();")

        wait.until(EC.url_contains('dashboard'))

        # สมชัยเข้าหน้า Public Results อีกครั้ง
        self.browser.get(self.live_server_url + '/results/')
        
        # 🟢 สั่งให้บอทลองคลิกแท็บ "ผล ส.ส. เขต"
        try:
            constituency_tab = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'ผล ส.ส. เขต')]")))
            self.browser.execute_script("arguments[0].click();", constituency_tab)
            time.sleep(1)
        except:
            pass

        public_results_body = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        public_results_text = public_results_body.get_attribute('textContent')
        
        self.assertIn('พรรคก้าวหน้า', public_results_text)
        self.assertIn('นายใจดี สู้ศึก', public_results_text)