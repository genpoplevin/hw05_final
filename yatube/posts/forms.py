from django import forms

from posts.models import Comment, Group, Post


class PostForm(forms.ModelForm):
    group = forms.ModelChoiceField(queryset=Group.objects,
                                   empty_label='Группа не выбрана',
                                   required=False,
                                   label='Группа')

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
