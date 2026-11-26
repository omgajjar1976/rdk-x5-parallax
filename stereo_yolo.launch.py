# Run on the RDK X5:  source /opt/tros/humble/setup.bash && ros2 launch ~/stage1/stereo_yolo.launch.py
# Then open http://<board-ip>:8000 : left camera on top, boxes labelled "<class> <distance>m".
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def include(pkg, path, **args):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(get_package_share_directory(pkg), path)),
        launch_arguments={k: v if isinstance(v, LaunchConfiguration) else str(v) for k, v in args.items()}.items())


def generate_launch_description():
    here = os.path.dirname(os.path.abspath(__file__))
    return LaunchDescription([
        DeclareLaunchArgument('fps', default_value='30.0'),
        include('hobot_shm', 'launch/hobot_shm.launch.py'),
        include('mipi_cam', 'launch/mipi_cam_dual_channel.launch.py',
                mipi_image_width=1280, mipi_image_height=1088,
                mipi_image_framerate=LaunchConfiguration('fps'),
                device_mode='dual', dual_combine=2, mipi_channel=2, mipi_channel2=0,
                # EEPROM calibration angle is 90; output turn = rotation - 90, so 90 keeps disparity horizontal
                mipi_rotation=90.0,
                mipi_frame_ts_type='realtime'),   # system clock stamps, so latency can be measured
        include('hobot_codec', 'launch/hobot_codec_encode.launch.py',
                codec_in_mode='ros', codec_out_mode='ros', codec_jpg_quality=80.0,
                codec_sub_topic='/image_combine_raw', codec_pub_topic='/image_combine_jpeg'),
        include('websocket', 'launch/websocket.launch.py',
                websocket_image_topic='/image_combine_jpeg',
                websocket_smart_topic='/stereo_yolo/detections',
                websocket_only_show_image='False'),
        ExecuteProcess(cmd=['python3', os.path.join(here, 'stereo_yolo_node.py')], output='screen'),
    ])
