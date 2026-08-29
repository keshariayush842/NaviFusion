import rclpy
from rclpy.node import Node

import numpy as np
import time
import csv
import os

from sensor_msgs.msg import Imu, NavSatFix
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped


class NaviFusionEKFNode(Node):

    def __init__(self):
        super().__init__('navifusion_ekf_node')

        # ============================================================
        # ROS SUBSCRIPTIONS
        # ============================================================

        self.create_subscription(
            Imu,
            '/imu/data',
            self.imu_callback,
            10
        )

        self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.create_subscription(
            NavSatFix,
            '/gps/fix',
            self.gps_callback,
            10
        )

        # ============================================================
        # ROS PUBLISHERS
        # ============================================================

        self.ekf_pose_pub = self.create_publisher(
            PoseStamped,
            '/navifusion/ekf_pose',
            10
        )

        self.imu_pose_pub = self.create_publisher(
            PoseStamped,
            '/navifusion/imu_only_pose',
            10
        )

        # ============================================================
        # EKF STATE
        #
        # state =
        # [x, y, heading, velocity]
        # ============================================================

        self.state = np.array([
            0.0,
            0.0,
            0.0,
            0.0
        ], dtype=float)

        self.P = np.eye(4) * 0.1

        # Process noise
        self.Q = np.diag([
            0.01,
            0.01,
            0.01,
            0.05
        ])

        # ============================================================
        # IMU DEAD RECKONING STATE
        # ============================================================

        self.imu_x = 0.0
        self.imu_y = 0.0
        self.imu_theta = 0.0

        # ============================================================
        # REFERENCE GPS COORDINATE
        # ============================================================

        self.lat_origin = 12.9692
        self.lon_origin = 79.1559

        # ============================================================
        # GNSS STATUS
        # ============================================================

        self.last_gps_time = time.time()
        self.gnss_active = False

        self.gnss_rejected = False

        self.gnss_mahalanobis = 0.0
        self.last_gnss_decision = "NONE"

        # ============================================================
        # PHASE 2A
        # NAVIGATION INTELLIGENCE
        # ============================================================

        self.navigation_state = "STARTING"

        self.navigation_reason = (
            "System starting"
        )

        # Consecutive anomaly counter
        self.gnss_anomaly_count = 0

        # Consecutive normal measurements
        self.gnss_normal_count = 0

        # Number of severe anomalies needed
        # before calling it a spoofing suspicion
        self.spoofing_threshold_count = 3

        # Mahalanobis levels
        self.degraded_threshold = 9.21
        self.spoofing_threshold = 50.0

        # ============================================================
        # TELEMETRY
        # ============================================================

        self.csv_file_path = os.path.expanduser(
            '~/navifusion_ws/live_telemetry.csv'
        )

        self.csv_file = open(
            self.csv_file_path,
            mode='w',
            newline=''
        )

        self.csv_writer = csv.writer(self.csv_file)

        self.csv_writer.writerow([
            'timestamp',
            'ekf_x',
            'ekf_y',
            'imu_x',
            'imu_y',
            'gnss_status',
            'drift_error',
            'gnss_mahalanobis',
            'gnss_decision',
            'navigation_state',
            'navigation_reason',
            'anomaly_count'
        ])

        self.csv_file.flush()

        # ============================================================
        # TIMERS
        # ============================================================

        self.create_timer(
            0.5,
            self.diagnostics_callback
        )

        self.create_timer(
            0.1,
            self.publish_poses
        )

        # ============================================================
        # STARTUP
        # ============================================================

        self.get_logger().info(
            'NaviFusion Adaptive EKF Engine Online!'
        )

        self.get_logger().info(
            'GNSS Mahalanobis anomaly detector ENABLED'
        )

        self.get_logger().info(
            'Phase 2A Navigation Intelligence ENABLED'
        )

    # ================================================================
    # IMU CALLBACK
    # ================================================================

    def imu_callback(self, msg: Imu):

        dt = 0.1

        angular_velocity = msg.angular_velocity.z

        self.imu_theta += angular_velocity * dt

        # For the simulator, approximate vehicle speed
        # using 1 m/s forward motion.
        speed = 1.0

        self.imu_x += (
            speed
            * np.cos(self.imu_theta)
            * dt
        )

        self.imu_y += (
            speed
            * np.sin(self.imu_theta)
            * dt
        )

    # ================================================================
    # ODOMETRY CALLBACK
    # ================================================================

    def odom_callback(self, msg: Odometry):

        dt = 0.1

        velocity = msg.twist.twist.linear.x
        angular_velocity = msg.twist.twist.angular.z

        theta = self.state[2]

        # Prediction step
        self.state[0] += (
            velocity
            * np.cos(theta)
            * dt
        )

        self.state[1] += (
            velocity
            * np.sin(theta)
            * dt
        )

        self.state[2] += (
            angular_velocity * dt
        )

        self.state[3] = velocity

        # Normalize heading
        self.state[2] = np.arctan2(
            np.sin(self.state[2]),
            np.cos(self.state[2])
        )

        # Increase covariance during prediction
        self.P = self.P + self.Q

    # ================================================================
    # GPS CALLBACK
    # ================================================================

    def gps_callback(self, msg: NavSatFix):

        # GPS is available
        self.last_gps_time = time.time()
        self.gnss_active = True

        # ============================================================
        # CONVERT GPS LAT/LON → LOCAL XY METERS
        # ============================================================

        dlat = (
            msg.latitude
            - self.lat_origin
        )

        dlon = (
            msg.longitude
            - self.lon_origin
        )

        gps_y = dlat * 111111.0

        gps_x = (
            dlon
            * (
                111111.0
                * np.cos(
                    np.radians(self.lat_origin)
                )
            )
        )

        measurement = np.array([
            gps_x,
            gps_y
        ])

        # ============================================================
        # MEASUREMENT MODEL
        # ============================================================

        H = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ])

        # GNSS measurement noise
        R = np.eye(2) * 0.5

        # ============================================================
        # INNOVATION
        # ============================================================

        predicted_measurement = H @ self.state

        innovation = (
            measurement
            - predicted_measurement
        )

        S = (
            H @ self.P @ H.T
            + R
        )

        # ============================================================
        # MAHALANOBIS DISTANCE
        # ============================================================

        try:

            mahalanobis = float(
                innovation.T
                @ np.linalg.inv(S)
                @ innovation
            )

        except np.linalg.LinAlgError:

            mahalanobis = float('inf')

        self.gnss_mahalanobis = mahalanobis

        # ============================================================
        # PHASE 2A INTELLIGENCE
        #
        # Decide whether GPS is trustworthy.
        # ============================================================

        if mahalanobis > self.degraded_threshold:

            # --------------------------------------------------------
            # ABNORMAL GNSS MEASUREMENT
            # --------------------------------------------------------

            self.gnss_rejected = True

            self.last_gnss_decision = "REJECTED"

            self.gnss_anomaly_count += 1
            self.gnss_normal_count = 0

            # --------------------------------------------------------
            # SEVERE ANOMALY
            # --------------------------------------------------------

            if (
                mahalanobis
                >= self.spoofing_threshold
            ):

                self.navigation_reason = (
                    "Severe GNSS position anomaly"
                )

            else:

                self.navigation_reason = (
                    "GNSS inconsistent with predicted trajectory"
                )

            # --------------------------------------------------------
            # STATE CLASSIFICATION
            # --------------------------------------------------------

            if (
                self.gnss_anomaly_count
                >= self.spoofing_threshold_count
            ):

                self.navigation_state = (
                    "SPOOFING_SUSPECTED"
                )

            else:

                self.navigation_state = (
                    "GNSS_DEGRADED"
                )

            self.get_logger().warn(
                '[NAV INTELLIGENCE] '
                f'State={self.navigation_state} | '
                f'Mahalanobis={mahalanobis:.2f} | '
                f'Anomalies={self.gnss_anomaly_count}'
            )

            # IMPORTANT:
            # Do NOT update EKF with bad GPS.
            return

        # ============================================================
        # GNSS MEASUREMENT ACCEPTED
        # ============================================================

        self.gnss_rejected = False

        self.last_gnss_decision = "ACCEPTED"

        self.gnss_anomaly_count = 0
        self.gnss_normal_count += 1

        self.navigation_state = "NORMAL"

        self.navigation_reason = (
            "GNSS consistent with predicted trajectory"
        )

        # ============================================================
        # KALMAN GAIN
        # ============================================================

        try:

            K = (
                self.P
                @ H.T
                @ np.linalg.inv(S)
            )

        except np.linalg.LinAlgError:

            return

        # ============================================================
        # EKF UPDATE
        # ============================================================

        self.state = (
            self.state
            + K @ innovation
        )

        self.P = (
            np.eye(4)
            - K @ H
        ) @ self.P

        # Keep covariance numerically stable
        self.P = (
            self.P
            + self.P.T
        ) / 2.0

        self.get_logger().info(
            '[GNSS FUSED] '
            f'X={self.state[0]:.2f}m '
            f'Y={self.state[1]:.2f}m '
            f'Mahalanobis={mahalanobis:.2f}',
            throttle_duration_sec=2.0
        )

    # ================================================================
    # PUBLISH POSES
    # ================================================================

    def publish_poses(self):

        now = self.get_clock().now().to_msg()

        # ============================================================
        # EKF POSE
        # ============================================================

        ekf_msg = PoseStamped()

        ekf_msg.header.stamp = now
        ekf_msg.header.frame_id = 'map'

        ekf_msg.pose.position.x = float(
            self.state[0]
        )

        ekf_msg.pose.position.y = float(
            self.state[1]
        )

        ekf_msg.pose.position.z = 0.0

        # Convert heading → quaternion
        theta = self.state[2]

        ekf_msg.pose.orientation.x = 0.0
        ekf_msg.pose.orientation.y = 0.0

        ekf_msg.pose.orientation.z = float(
            np.sin(theta / 2.0)
        )

        ekf_msg.pose.orientation.w = float(
            np.cos(theta / 2.0)
        )

        self.ekf_pose_pub.publish(
            ekf_msg
        )

        # ============================================================
        # IMU-ONLY POSE
        # ============================================================

        imu_msg = PoseStamped()

        imu_msg.header.stamp = now
        imu_msg.header.frame_id = 'map'

        imu_msg.pose.position.x = float(
            self.imu_x
        )

        imu_msg.pose.position.y = float(
            self.imu_y
        )

        imu_msg.pose.position.z = 0.0

        imu_msg.pose.orientation.x = 0.0
        imu_msg.pose.orientation.y = 0.0

        imu_msg.pose.orientation.z = float(
            np.sin(self.imu_theta / 2.0)
        )

        imu_msg.pose.orientation.w = float(
            np.cos(self.imu_theta / 2.0)
        )

        self.imu_pose_pub.publish(
            imu_msg
        )

    # ================================================================
    # DIAGNOSTICS + INTELLIGENCE
    # ================================================================

    def diagnostics_callback(self):

        now = time.time()

        # ============================================================
        # CALCULATE DRIFT
        # ============================================================

        drift_error = np.sqrt(
            (
                self.state[0]
                - self.imu_x
            ) ** 2
            +
            (
                self.state[1]
                - self.imu_y
            ) ** 2
        )

        # ============================================================
        # GNSS OUTAGE DETECTION
        # ============================================================

        gps_timeout = (
            now
            - self.last_gps_time
        ) > 1.5

        if gps_timeout:

            self.gnss_active = False

            status_str = "OUTAGE"

            self.navigation_state = (
                "GNSS_OUTAGE"
            )

            self.navigation_reason = (
                "GNSS signal unavailable - "
                "using IMU + ODOM"
            )

            self.last_gnss_decision = (
                "UNAVAILABLE"
            )

            self.get_logger().warn(
                '[OUTAGE MODE] '
                f'Drift={drift_error:.2f} m | '
                'Navigation=IMU + ODOM',
                throttle_duration_sec=2.0
            )

        else:

            self.gnss_active = True

            status_str = "ACTIVE"

            # --------------------------------------------------------
            # IMPORTANT:
            #
            # Don't overwrite SPOOFING_SUSPECTED or
            # GNSS_DEGRADED here.
            #
            # GPS callback already decided the state.
            # --------------------------------------------------------

            if (
                self.navigation_state
                == "SPOOFING_SUSPECTED"
            ):

                self.get_logger().warn(
                    '[SPOOFING SUSPECTED] '
                    f'Mahalanobis='
                    f'{self.gnss_mahalanobis:.2f}',
                    throttle_duration_sec=2.0
                )

            elif (
                self.navigation_state
                == "GNSS_DEGRADED"
            ):

                self.get_logger().warn(
                    '[GNSS DEGRADED] '
                    f'Mahalanobis='
                    f'{self.gnss_mahalanobis:.2f}',
                    throttle_duration_sec=2.0
                )

            else:

                self.get_logger().info(
                    '[NAVIGATION NORMAL] '
                    f'EKF X={self.state[0]:.2f} '
                    f'Y={self.state[1]:.2f}',
                    throttle_duration_sec=2.0
                )

        # ============================================================
        # WRITE TELEMETRY
        # ============================================================

        self.csv_writer.writerow([
            now,
            self.state[0],
            self.state[1],
            self.imu_x,
            self.imu_y,
            status_str,
            drift_error,
            self.gnss_mahalanobis,
            self.last_gnss_decision,
            self.navigation_state,
            self.navigation_reason,
            self.gnss_anomaly_count
        ])

        self.csv_file.flush()

    # ================================================================
    # CLEAN SHUTDOWN
    # ================================================================

    def destroy_node(self):

        try:

            if not self.csv_file.closed:
                self.csv_file.close()

        except Exception:
            pass

        super().destroy_node()


# ====================================================================
# MAIN
# ====================================================================

def main(args=None):

    rclpy.init(args=args)

    node = NaviFusionEKFNode()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        try:

            if rclpy.ok():
                rclpy.shutdown()

        except Exception:
            pass


if __name__ == '__main__':
    main()
