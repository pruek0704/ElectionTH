from django.core.management.base import BaseCommand, CommandError
from voting.models import User


class Command(BaseCommand):
    help = 'เพิ่มผู้ใช้ประชาชน (Citizen) เข้าระบบเลือกตั้ง'

    def add_arguments(self, parser):
        parser.add_argument('national_id', type=str, help='เลขบัตรประชาชน 13 หลัก')
        parser.add_argument('first_name', type=str, help='ชื่อจริง')
        parser.add_argument('last_name', type=str, help='นามสกุล')

    def handle(self, *args, **options):
        nid = options['national_id'].strip()
        fname = options['first_name'].strip()
        lname = options['last_name'].strip()

        # Validate
        if len(nid) != 13 or not nid.isdigit():
            raise CommandError(f'❌ เลขบัตรประชาชนต้องเป็น 13 หลัก ได้รับ: {nid}')

        if not fname or not lname:
            raise CommandError('❌ ชื่อ-นามสกุล ไม่ควรว่าง')

        if User.objects.filter(username=nid).exists():
            raise CommandError(f'❌ {nid} มีอยู่ในระบบแล้ว')

        # Create
        u = User.objects.create_user(
            username=nid,
            password=nid,
            first_name=fname,
            last_name=lname,
            national_id=nid,
            is_staff=False,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ สร้างผู้ใช้สำเร็จ: {u.get_full_name()} ({nid})'
            )
        )
