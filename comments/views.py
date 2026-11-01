"""Страницы комментариев: данные получаются через Django ORM."""

from django.shortcuts import get_object_or_404, render

from comments.models import Comment


def comments(request):
    """Страница /comments/: комментарии с макетом и автором."""
    comments_list = Comment.objects.select_related(
        "layout",
        "author",
    ).order_by("-comment_date", "pk")

    context = {"comments": comments_list}
    return render(request, "comments/comment_list.html", context)


def comment_detail(request, comment_id):
    """Страница /comments/<id>/: карточка комментария или ответ 404."""
    comment = get_object_or_404(
        Comment.objects.select_related("layout", "author"),
        pk=comment_id,
    )

    context = {"comment": comment}
    return render(request, "comments/comment_detail.html", context)
