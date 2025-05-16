import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from api.models import Category, Task
from django.urls import reverse

@pytest.mark.django_db
def test_create_category(api_client_with_user):
    response = api_client_with_user.post('/api/categories/', {'name': 'Test Category'}, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert Category.objects.count() == 1
    assert Category.objects.get().name == 'Test Category'


@pytest.fixture
def api_client_with_user(db):
    user = User.objects.create_user(username='testuser', password='testpassword')
    client = APIClient()
    client.force_authenticate(user=user)
    return client
  

def test_create_category_invalid(api_client_with_user):
    response = api_client_with_user.post('/api/categories/', {'name': ''}, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_task(api_client_with_user):
    # First, create a category for the task
    user = User.objects.get(username='testuser')
    category = Category.objects.create(name='Work', owner=user)

    # Prepare task data
    data = {
        'title': 'Do homework',
        'priority': 'medium',
        'category_id': category.id
    }

    response = api_client_with_user.post('/api/tasks/', data, format='json')

    print(response.status_code)  # 👈 Add this
    print(response.data)

    assert response.status_code == status.HTTP_201_CREATED
    assert Task.objects.count() == 1
    task = Task.objects.first()
    assert task.title == 'Do homework'
    assert task.category == category
    assert task.owner == user

@pytest.mark.django_db
def test_create_task_missing_priority(api_client_with_user):
    user = User.objects.get(username='testuser')
    category = Category.objects.create(name='Urgent', owner=user)

    data = {
        'title': 'Fix bug',
        'category_id': category.id
        # 'priority' is missing
    }

    response = api_client_with_user.post('/api/tasks/', data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'priority' in response.data

@pytest.mark.django_db
def test_create_task_title_too_long(api_client_with_user):
    user = User.objects.get(username='testuser')
    category = Category.objects.create(name='General', owner=user)

    long_title = 'A' * 201  # 201 characters
    data = {
        'title': long_title,
        'priority': 'low',
        'category_id': category.id
    }

    response = api_client_with_user.post('/api/tasks/', data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'title' in response.data

@pytest.mark.django_db
def test_create_task_invalid_priority(api_client_with_user):
    user = User.objects.get(username='testuser')
    category = Category.objects.create(name='Errands', owner=user)

    data = {
        'title': 'Invalid priority task',
        'priority': 'urgent',  # ❌ not in choices
        'category_id': category.id
    }

    response = api_client_with_user.post('/api/tasks/', data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'priority' in response.data

@pytest.mark.django_db
def test_create_task_missing_title(api_client_with_user):
    user = User.objects.get(username='testuser')
    category = Category.objects.create(name='Chores', owner=user)

    data = {
        # 'title' is missing here ❌
        'priority': 'low',
        'category_id': category.id
    }

    response = api_client_with_user.post('/api/tasks/', data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'title' in response.data  # we expect 'title' error in response



@pytest.mark.django_db
def test_filter_tasks_by_category(api_client_with_user):
    user = User.objects.get(username='testuser')
    category1 = Category.objects.create(name='Work', owner=user)
    category2 = Category.objects.create(name='Home', owner=user)

    # Create 2 tasks, each in a different category
    Task.objects.create(title='Task 1', priority='low', category=category1, owner=user)
    Task.objects.create(title='Task 2', priority='high', category=category2, owner=user)

    # Filter by category1
    response = api_client_with_user.get(f'/api/tasks/?category={category1.id}')

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['title'] == 'Task 1'

@pytest.mark.django_db
def test_filter_tasks_by_owner(api_client_with_user):
    # The authenticated user
    user1 = User.objects.get(username='testuser')
    category = Category.objects.create(name='Work', owner=user1)

    # Another user
    user2 = User.objects.create_user(username='otheruser', password='pass1234')

    # Tasks for both users
    Task.objects.create(title='My Task', priority='low', category=category, owner=user1)
    Task.objects.create(title='Other User Task', priority='high', category=category, owner=user2)

    # Authenticated as user1
    response = api_client_with_user.get('/api/tasks/')

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['title'] == 'My Task'

@pytest.mark.django_db
def test_update_task(api_client_with_user):
    user = User.objects.get(username='testuser')
    category = Category.objects.create(name='Chores', owner=user)

    task = Task.objects.create(
        title='Clean room',
        priority='low',
        category=category,
        owner=user,
        completed=False
    )

    # New data to update
    update_data = {
        'title': 'Clean the room thoroughly',
        'completed': True,
        'priority': 'high',
        'category_id': category.id
    }

    url = f'/api/tasks/{task.id}/'
    response = api_client_with_user.put(url, update_data, format='json')

    assert response.status_code == 200
    assert response.data['title'] == 'Clean the room thoroughly'
    assert response.data['completed'] is True
    assert response.data['priority'] == 'high'


@pytest.mark.django_db
def test_update_task_by_another_user(api_client_with_user):
    # Create another user
    other_user = User.objects.create_user(username='otheruser', password='otherpass')
    category = Category.objects.create(name='Private', owner=other_user)

    # Create a task owned by other_user
    task = Task.objects.create(
        title='Secret task',
        priority='high',
        category=category,
        owner=other_user,
        completed=False
    )

    # Try to update it as testuser (not the owner)
    update_data = {
        'title': 'Hacked task',
        'priority': 'low',
        'completed': True,
        'category_id': category.id
    }

    url = f'/api/tasks/{task.id}/'
    response = api_client_with_user.put(url, update_data, format='json')

    # Should NOT allow update
    assert response.status_code == 404  # or 403 if custom permissions


@pytest.mark.django_db
def test_delete_task(api_client_with_user):
    # Get the test user
    user = User.objects.get(username='testuser')

    # Create a category and task
    category = Category.objects.create(name='ToDelete', owner=user)
    task = Task.objects.create(
        title='Delete me',
        priority='low',
        category=category,
        owner=user,
        completed=False
    )

    # Send DELETE request
    url = f'/api/tasks/{task.id}/'
    response = api_client_with_user.delete(url)

    # Expect status code 204 (No Content)
    assert response.status_code == 204

    # Confirm task is deleted
    assert not Task.objects.filter(id=task.id).exists()

@pytest.mark.django_db
def test_delete_task(api_client_with_user):
    # Get the test user
    user = User.objects.get(username='testuser')

    # Create a category and task
    category = Category.objects.create(name='ToDelete', owner=user)
    task = Task.objects.create(
        title='Delete me',
        priority='low',
        category=category,
        owner=user,
        completed=False
    )

    # Send DELETE request
    url = f'/api/tasks/{task.id}/'
    response = api_client_with_user.delete(url)

    # Expect status code 204 (No Content)
    assert response.status_code == 204

    # Confirm task is deleted
    assert not Task.objects.filter(id=task.id).exists()


@pytest.mark.django_db
def test_cannot_delete_other_users_task(api_client_with_user):
    # Create a second user
    other_user = User.objects.create_user(username='otheruser', password='12345678')
    category = Category.objects.create(name='Other Cat', owner=other_user)

    # Create a task for the other user
    task = Task.objects.create(
        title='Not yours',
        priority='high',
        category=category,
        owner=other_user
    )

    # Try to delete the task with first user
    url = f'/api/tasks/{task.id}/'
    response = api_client_with_user.delete(url)

    # Should return 403 Forbidden
    assert response.status_code in [403, 404]

    # Task should still exist
    assert Task.objects.filter(id=task.id).exists()


@pytest.mark.django_db
def test_user_can_update_own_task(api_client_with_user):
    user = User.objects.get(username='testuser')
    category = Category.objects.create(name='Updates', owner=user)

    task = Task.objects.create(
        title='Old Title',
        priority='low',
        category=category,
        owner=user
    )

    url = f'/api/tasks/{task.id}/'
    data = {
        'title': 'Updated Title',
        'priority': 'high',
        'category': category.id
    }

    response = api_client_with_user.put(url, data, format='json')

    assert response.status_code == 200
    assert response.data['title'] == 'Updated Title'
    assert response.data['priority'] == 'high'

    task.refresh_from_db()
    assert task.title == 'Updated Title'
    assert task.priority == 'high'

@pytest.mark.django_db
def test_user_cannot_update_others_task(api_client_with_user):
    # Create a second user and their task
    other_user = User.objects.create_user(username='otheruser2', password='12345678')
    category = Category.objects.create(name='Other Category', owner=other_user)
    task = Task.objects.create(
        title='Private Task',
        priority='low',
        category=category,
        owner=other_user
    )

    # Try to update it using the first (logged in) user
    url = f'/api/tasks/{task.id}/'
    data = {
        'title': 'Trying to Hack',
        'priority': 'high',
        'category': category.id
    }

    response = api_client_with_user.put(url, data, format='json')

    # You can accept either 403 or 404 depending on your logic
    assert response.status_code in [403, 404]