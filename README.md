# 🗳️ ElectionTH - ระบบลงคะแนนเลือกตั้งจำลอง
โปรเจคระบบเลือกตั้งที่พัฒนาด้วย Django พร้อมระบบป้องกันการลงคะแนนซ้ำและรองรับการจัดการโดยแอดมิน

## ✨ คุณสมบัติ
- ระบบล็อกอินประชาชนด้วยชื่อและเลขบัตรประชาชน
- ระบบโหวต ส.ส. เขต และพรรคการเมือง (Atomic Transaction)
- ระบบ Admin สำหรับเปิด-ปิดหีบ และดูผลคะแนนแบบเรียลไทม์
- Unit Test ครอบคลุม Logic สำคัญมากกว่า 10 รายการ

## 🛠️ วิธีติดตั้ง
1. ติดตั้ง Library: `pip install -r requirements.txt`
2. สร้างไฟล์ `.env` ตามแบบใน `.env.example`
3. Migrate ฐานข้อมูล: `python manage.py migrate`
4. รันโปรเจค: `python manage.py runserver`

## 🧪 การทดสอบ
รันคำสั่งเพื่อตรวจสอบระบบ:
`python manage.py test voting`
`python manage.py test functional_tests tests`