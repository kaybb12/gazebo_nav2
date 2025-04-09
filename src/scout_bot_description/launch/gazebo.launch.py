from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os

def generate_launch_description():
    pkg_share = FindPackageShare(package='scout_bot_description').find('scout_bot_description')
    default_model_path = os.path.join(pkg_share, 'src', 'description', 'scout_bot_description.urdf')
    default_rviz_config_path = os.path.join(pkg_share, 'rviz', 'config.rviz')
    
    # Robot State Publisher : URDF를 읽고 TF를 퍼블리시
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': Command(['xacro ', LaunchConfiguration('model')])}]
    )

    # Joint State Publisher : 여기서는 기본 모델 파일 경로만 인자로 전달
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        arguments=[default_model_path]
    )
    
    # Gazebo 실행 (필수 플러그인 포함)
    gazebo_process = ExecuteProcess(
        cmd=['gazebo', '--verbose', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so'],
        output='screen'
    )

    # Gazebo에 로봇(여기서는 scout_bot)을 스폰하는 노드
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'scout_bot', '-topic', 'robot_description'],
        output='screen'
    )

    # robot_localization의 ekf_node를 실행하여 센서 데이터를 융합하고 transform을 게시함
    robot_localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_node',
        output='screen',
        parameters=[os.path.join(pkg_share, 'config', 'ekf.yaml'),
                    {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    # RViz 실행
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rvizconfig')]
    )

    return LaunchDescription([
        # launch 인자 선언: 로봇 모델, RViz 설정, 그리고 use_sim_time
        DeclareLaunchArgument(
            name='model',
            default_value=default_model_path,
            description='Absolute path to robot model file'
        ),
        DeclareLaunchArgument(
            name='rvizconfig',
            default_value=default_rviz_config_path,
            description='Absolute path to rviz config file'
        ),
        DeclareLaunchArgument(
            name='use_sim_time',
            default_value='True',
            description='Flag to enable use_sim_time'
        ),
        # 실행 순서: Gazebo 실행 -> Joint State Publisher -> Robot State Publisher -> 로봇 스폰 -> 로봇 융합 (robot_localization) -> RViz 실행
        gazebo_process,
        joint_state_publisher_node,
        robot_state_publisher_node,
        spawn_entity,
        robot_localization_node,
        rviz_node
    ])
