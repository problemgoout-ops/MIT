from django.db import models


class Lead(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        CONTACTED = 'contacted', 'Связались'
        IN_PROGRESS = 'in_progress', 'В работе'
        CONVERTED = 'converted', 'Конвертирована'
        REJECTED = 'rejected', 'Отклонена'
        SPAM = 'spam', 'Спам'

    last_name = models.CharField('Фамилия', max_length=100)
    first_name = models.CharField('Имя', max_length=100)
    telegram = models.CharField('Telegram', max_length=100)
    email = models.EmailField('Email')
    task_description = models.TextField('Описание задачи', blank=True, default='')
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    manager_comment = models.TextField('Комментарий менеджера', blank=True, default='')
    source = models.CharField('Источник', max_length=200, blank=True, default='')
    utm_source = models.CharField('UTM Source', max_length=200, blank=True, default='')
    utm_medium = models.CharField('UTM Medium', max_length=200, blank=True, default='')
    utm_campaign = models.CharField('UTM Campaign', max_length=200, blank=True, default='')
    utm_content = models.CharField('UTM Content', max_length=200, blank=True, default='')
    utm_term = models.CharField('UTM Term', max_length=200, blank=True, default='')
    page_url = models.CharField('URL страницы', max_length=500, blank=True, default='')
    user_agent = models.TextField('User Agent', blank=True, default='')
    ip_address = models.GenericIPAddressField('IP адрес', blank=True, null=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.first_name} {self.last_name} — {self.get_status_display()}'
