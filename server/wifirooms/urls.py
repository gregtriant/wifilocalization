from django.urls import path, include
from rest_framework import routers
from . import views

# for rest framework API
router = routers.DefaultRouter()
router.register(r'floorPlans', views.FloorPlanViewSet, basename='floor-plans-list')
router.register(r'rooms', views.RoomViewSet, basename='rooms-list')
router.register(r'signalPoints', views.SignalPointViewSet, basename='signals-points-list')
router.register(r'routes', views.RouteViewSet, basename='routes-list')

app_name = 'wifirooms'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:floor_plan_id>/rooms/', views.rooms, name="rooms"),
    path('<int:floor_plan_id>/results/', views.results, name="results"),
    path('<int:floor_plan_id>/fingerprinting/', views.fingerprinting, name="fingerprinting"),

    path('<int:floor_plan_id>/radio_map/', views.radio_map, name="radio_map"),  # returns the radio map data frame in json
    path('<int:floor_plan_id>/bssids/', views.bssids, name="bssids"),  # returns the unique bssids of the floor_plan's radio map
    path('<int:floor_plan_id>/point_scans/', views.point_scans, name="point_scans"),  # returns the test points with their scans for the floor_plan's radio map
    path('<int:floor_plan_id>/test_points/', views.test_points, name="test_points"),  # returns the test points with their scans for the floor_plan's radio map
    path('<int:floor_plan_id>/all_scans/<int:point_index>', views.all_scans, name="all_scans"), # returns all the scans done on that point

    path('localize/classification_algorithms/', views.classification_algorithms, name="classification_algorithms"),
    path('localize/point/<int:floor_plan_id>/', views.localize_point, name="localize_point"),
    path('localize/room/<int:floor_plan_id>/', views.localize_room, name="localize_room"),
    path('localize/test_all/<int:floor_plan_id>/', views.localize_test_all, name="localize_test_all"),
    path('localize/localization_results/<int:floor_plan_id>/', views.localization_results, name="localization_results"),

    # paths for APIs
    path('api/', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
