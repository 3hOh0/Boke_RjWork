from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interaction', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='favoritefolder',
            name='pinned',
            field=models.BooleanField(default=False, verbose_name='pinned'),
        ),
        migrations.AddField(
            model_name='favoritefolder',
            name='sort_order',
            field=models.IntegerField(default=0, help_text='smaller number shows first; pinned folders always on top', verbose_name='sort order'),
        ),
        migrations.AddField(
            model_name='favoritefolder',
            name='tags',
            field=models.CharField(blank=True, help_text='comma separated tags, e.g. “django,python,后端”', max_length=120, verbose_name='tags'),
        ),
        migrations.AddField(
            model_name='favoriteitem',
            name='note_version',
            field=models.PositiveIntegerField(default=1, verbose_name='note version'),
        ),
        migrations.AddField(
            model_name='favoriteitem',
            name='updated_time',
            field=models.DateTimeField(auto_now=True, verbose_name='updated time'),
        ),
        migrations.AlterModelOptions(
            name='favoritefolder',
            options={'ordering': ['-pinned', 'sort_order', '-updated_time', '-created_time'], 'verbose_name': 'favorite folder', 'verbose_name_plural': 'favorite folders'},
        ),
        migrations.AddIndex(
            model_name='favoriteitem',
            index=models.Index(fields=['updated_time'], name='interaction_updated__idx'),
        ),
    ]

