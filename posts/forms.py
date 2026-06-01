from django import forms
from posts.models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'content', 'tags', 'is_published')
        labels = {
            'title': 'Заголовок',
            'content': 'Содержимое',
            'tags': 'Теги',
            'is_published': 'Опубликовать',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Заголовок поста', 'required': True, 'minlength': '3', 'maxlength': '255'}),
            'content': forms.Textarea(attrs={'rows': 8, 'placeholder': 'Текст поста...', 'required': True, 'minlength': '10'}),
            'tags': forms.TextInput(attrs={'placeholder': 'тег1, тег2, тег3', 'maxlength': '200'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        labels = {'content': ''}
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Написать комментарий...',
                'required': True,
                'minlength': '2',
                'maxlength': '2000',
            }),
        }
