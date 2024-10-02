from ping3 import ping
from django.core.management.base import BaseCommand, CommandError
from main.models import LogOwnerModel, LogItemModel


class Command(BaseCommand):
    help = 'Site monitoring'

    def handle(self, *args, **options):
        sites = LogOwnerModel.objects.all()

        for item in sites:
            if item.site_url is None:
                continue
            site_host = item.site_url.replace('http://', '').replace('https://', '').split('/')[0]
            ping_seconds = ping(site_host, timeout=5)
            if ping_seconds is False:
                log_item = LogItemModel(owner=item, name='CRASH')
                log_item.save()
                self.stdout.write(
                    self.style.ERROR(f"Ping {site_host}: FAIL")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Ping {site_host}: {ping_seconds}")
                )

        self.stdout.write(
            self.style.SUCCESS('Done')
        )
