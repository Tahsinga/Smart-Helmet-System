from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create demo admin and worker accounts for monitoring"

    def handle(self, *args, **options):
        User = get_user_model()

        admin_user, admin_created = User.objects.get_or_create(
            username="user1",
            defaults={
                "is_staff": True,
                "is_superuser": True,
                "email": "user1@example.com",
            },
        )
        if admin_created:
            admin_user.set_password("password")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: user1 / password"))
        else:
            changed = False
            if not admin_user.is_staff:
                admin_user.is_staff = True
                changed = True
            if not admin_user.is_superuser:
                admin_user.is_superuser = True
                changed = True
            if changed:
                admin_user.save()
            self.stdout.write(self.style.SUCCESS("Admin user already exists: user1"))

        worker_user, worker_created = User.objects.get_or_create(
            username="user2",
            defaults={
                "is_staff": False,
                "is_superuser": False,
                "email": "user2@example.com",
            },
        )
        if worker_created:
            worker_user.set_password("password")
            worker_user.save()
            self.stdout.write(self.style.SUCCESS("Created worker user: user2 / password"))
        else:
            if not worker_user.check_password("password"):
                worker_user.set_password("password")
                worker_user.save()
                self.stdout.write(self.style.SUCCESS("Updated password for worker user2"))
            else:
                self.stdout.write(self.style.SUCCESS("Worker user already exists: user2"))

        from monitoring.models import Worker, HelmetDevice

        worker_profile = Worker.objects.filter(user__isnull=True, helmetdevice__isnull=False).first()
        if worker_profile is None:
            worker_profile = Worker.objects.filter(user__isnull=True).first()

        if worker_profile is None:
            worker_profile = Worker.objects.create(
                user=worker_user,
                name="Demo Worker",
                employee_id="EMP002",
                department="Operations",
            )
            helmet, helmet_created = HelmetDevice.objects.get_or_create(
                device_id="HELMET_USER2",
                defaults={"battery_level": 100, "worker": worker_profile},
            )
            if not helmet_created:
                helmet.worker = worker_profile
                helmet.save(update_fields=["worker"])
            self.stdout.write(self.style.SUCCESS("Created a new worker profile and assigned HELMET_USER2."))
        else:
            if worker_profile.user is None:
                worker_profile.user = worker_user
                worker_profile.save(update_fields=["user"])
                self.stdout.write(self.style.SUCCESS(f"Assigned existing worker profile '{worker_profile.name}' to user2."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Existing worker profile '{worker_profile.name}' is already linked."))

            helmet = HelmetDevice.objects.filter(worker=worker_profile).first()
            if helmet:
                self.stdout.write(self.style.SUCCESS(f"Worker user2 will use helmet {helmet.device_id}."))
            else:
                unassigned_helmet = HelmetDevice.objects.filter(worker__isnull=True).first()
                if unassigned_helmet:
                    unassigned_helmet.worker = worker_profile
                    unassigned_helmet.save(update_fields=["worker"])
                    self.stdout.write(self.style.SUCCESS(f"Assigned helmet {unassigned_helmet.device_id} to user2."))
                else:
                    helmet = HelmetDevice.objects.create(
                        device_id="HELMET_USER2",
                        battery_level=100,
                        worker=worker_profile,
                    )
                    self.stdout.write(self.style.SUCCESS("Created and assigned new helmet HELMET_USER2 to user2."))
