#!/usr/bin/env python
import rospy
from std_srvs.srv import Trigger, TriggerResponse
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
import tf2_ros
import tf2_geometry_msgs
import numpy as np
from geometry_msgs.msg import Quaternion
import tf_conversions


class MpcPathPublisher:
    def __init__(self):
        self.path_publisher_ = rospy.Publisher("/mpc_trajectory_standalone", Path, queue_size=1, latch=False)
        self.pose_subscriber_ = rospy.Subscriber("/move_base_simple/goal", PoseStamped, self.receiveGoalPose)

        self.control_frame_ = rospy.get_param("control_frame", "world")
        self.robot_base_link_ = rospy.get_param("base_frame", "base")

        self.tf_buffer_ = tf2_ros.Buffer(rospy.Duration(1200))
        self.tf_listener_ = tf2_ros.TransformListener(self.tf_buffer_)

    def receiveGoalPose(self, goalPose):
        # type: (MpcPathPublisher, PoseStamped) -> bool
        path = Path()
        path.header.frame_id = self.control_frame_
        path.header.stamp = rospy.Time.now()

        try:
            baseLocation = self.tf_buffer_.lookup_transform(self.control_frame_,  # target frame
                                                            self.robot_base_link_,  # source frame
                                                            rospy.Time(0),  # get the tf at first available time
                                                            rospy.Duration(1))  # wait for 1 second
            startPose = PoseStamped()
            startPose.header.frame_id = self.control_frame_
            startPose.header.stamp = rospy.Time.now()
            startPose.pose.position = baseLocation.transform.translation
            startPose.pose.orientation = baseLocation.transform.rotation
            path.poses.append(startPose)

            targetFrameTransform = self.tf_buffer_.lookup_transform(self.control_frame_,  # target frame
                                                                    goalPose.header.frame_id,  # source frame
                                                                    rospy.Time(0),  # get the tf at first available time
                                                                    rospy.Duration(1))  # wait for 1 second

            goalPose = tf2_geometry_msgs.do_transform_pose(goalPose, targetFrameTransform)
            goalPose.header.stamp = rospy.Time.now()
            path.poses.append(goalPose)

            self.path_publisher_.publish(path)


        except (tf2_ros.LookupException, tf2_ros.ConnectivityException):
            rospy.logwarn(
                "[MpcPathPublisher] " + self.control_frame_ + " to " + self.robot_base_link_ + " not available.")
            return False

        return True

if __name__ == "__main__":
    rospy.init_node("mpc_path_publisher")
    mpcPathPublisher = MpcPathPublisher()
    rospy.spin()