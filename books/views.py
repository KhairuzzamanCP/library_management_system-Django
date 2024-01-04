from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import redirect,get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import DetailView,View,ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from books.models import Book, BorrowedBook,Comment
from books.forms import CommentForm
from django.utils import timezone
from transactions.views import send_email

# Create your views here.
class BookDetailsView(LoginRequiredMixin,DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name= 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        comments = book.comments.all()
        context['form'] = CommentForm()
        context['comments'] = comments
        return context

    def post(self, request, *args, **kwargs):
        book = self.get_object()
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.book = book
            comment.save()
            return redirect('details', pk=book.id)

        
        return self.render_to_response(self.get_context_data(form=form))

class BookBorrowView(LoginRequiredMixin,View):
    def get(self,request,id, **kwargs):
        book = get_object_or_404(Book, id = id)
        user = self.request.user
        if user.account.balance > book.borrowed_price:
            user.account.balance -= book.borrowed_price
            messages.success(request, 'book borrowed successful')
            user.account.save(update_fields=['balance'])
            BorrowedBook.objects.create(
                book = book,
                user = request.user.account,
                created_on=timezone.now(),
            )
            send_email(user,book.borrowed_price, 'borrow', 'Book Borrow Message','transactions/email_template.html')
            return redirect('borrow_book_lists') 
        else:
            messages.error(request, 'Insufficient balance to borrow the book')
            return redirect('home')

class BorrowBookListView(LoginRequiredMixin, ListView):
    model = BorrowedBook
    template_name = 'books/borrowed_book.html'
    context_object_name= 'borrowed_books'

    def get_queryset(self):
        user_id = self.request.user.id
        queryset = BorrowedBook.objects.filter(user__user_id = user_id)
        return queryset

class BookReturnView(LoginRequiredMixin, View):
    def get(self,request,id, **kwargs):
        book = get_object_or_404(BorrowedBook, id = id)
        user = self.request.user
        user.account.balance += book.book.borrowed_price
        messages.success(request, 'book return successful')
        user.account.save(update_fields=['balance'])
        send_email(user,book.book.borrowed_price, 'return_book', 'Book Return Message','transactions/email_template.html')
        book.delete()
        return redirect('borrow_book_lists') 
        


