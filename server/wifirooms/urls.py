from django.urls import path, include
from rest_framework import routers
from . import views

# for rest framework API
router = routers.DefaultRouter()
router.register(r'floorPlans', views.FloorPlanViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'signalPoints', views.SignalPointViewSet)
router.register(r'routes', views.RouteViewSet)

app_name = 'wifirooms'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:floor_plan_id>/rooms/', views.rooms, name="rooms"),
    path('<int:floor_plan_id>/fingerprinting/', views.fingerprinting, name="fingerprinting"),

    path('localize/knn/', views.knn, name="knn"),

    # paths for APIs
    path('api/', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
