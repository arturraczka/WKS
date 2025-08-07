from datetime import timedelta

from django.db import models

from apps.form.helpers import calculate_previous_weekday


class SingletonModel(models.Model):
	"""
	SingletonModel is a base class for models that should have only one
	instance, like application-wide config.

	To use it, subclass the `SingletonModel` class and use your model instance
	by calling MyCustomModel.load(). If it doesn't exist, it will be created
	automatically.

	Note: Make sure to have default values for all of your fields.
	"""
	class Meta:
		abstract = True

	def save(self, *args, **kwargs):
		self.pk = 1
		super().save(*args, **kwargs)

	def delete(self, *args, **kwargs):
		pass

	@classmethod
	def load(cls):
		obj, _ = cls.objects.get_or_create(pk=1)  # type: ignore[attr-defined]
		return obj


class AppConfig(SingletonModel):
	reports_start_day = models.DateTimeField("Początkowa data raportów", null=True, blank=True, help_text="Użyj tego pola, aby zmienić początkową datę i godzinę 7-dniowego przedziału dla którego generowane są raporty. Domyślna data i godzina rozpoczęcia przedziału to ostatnia sobota o 1 w nocy. Chcąc sprawdzić raport dla archiwalnego tygodnia należy wybrać sobotę, od której zacznie się raport, oraz godzinę 1:00 w nocy i zapisać. Po sprawdzeniu archiwalnego tygodnia należy wykasować wartość tego pola i zapisać, aby przywrócić funkcjonowanie raportów!!!")

	class Meta:
		verbose_name = "Konfiguracja Aplikacji"
		verbose_name_plural = "Konfiguracja Aplikacji"

	def __str__(self):
		return "Konfiguracja Aplikacji"

	@property
	def report_interval_start(self):
		return self.reports_start_day or calculate_previous_weekday()

	@property
	def report_interval_end(self):
		return self.report_interval_start + timedelta(days=7)
