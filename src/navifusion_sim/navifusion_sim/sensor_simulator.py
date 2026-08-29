import rclpy
from rclpy.node import Node
import numpy as np
import time

from sensor_msgs.msg import Imu, NavSatFix
from nav_msgs.msg import Odometry


class NaviFusionSensorSimulator(Node):

    def __init__(self):
        super().__init__('navifusion_sensor_simulator')

        # ============================================================
        # PUBLISHERS
        # ============================================================

        self.imu_pub = self.create_publisher(
            Imu,
            '/imu/data',
            10
        )

        self.odom_pub = self.create_publisher(
            Odometry,
            '/odom',
            10
        )

        self.gps_pub = self.create_publisher(
            NavSatFix,
            '/gps/fix',
            10
        )

        # 10 Hz simulation
        self.timer = self.create_timer(
            0.1,
            self.timer_callback
        )

        self.start_time = time.time()

        # ============================================================
        # GROUND TRUTH STATE
        # ============================================================

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        # ============================================================
        # GPS REFERENCE
        # ============================================================

        self.lat_origin = 12.9692
        self.lon_origin = 79.1559

        self.get_logger().info(
            'NaviFusion Sensor & Failure-Injection Simulator Online!'
        )

        self.get_logger().info(
            'Scenario: NORMAL -> GNSS ANOMALY -> OUTAGE -> RECOVERY'
        )

    # ================================================================
    # MAIN SIMULATION LOOP
    # ================================================================

    def timer_callback(self):

        elapsed = time.time() - self.start_time

        dt = 0.1

        # ============================================================
        # VEHICLE MOTION
        # ============================================================

        v = 1.0
        w = 0.1

        self.theta += w * dt

        self.x += (
            v *
            np.cos(self.theta) *
            dt
        )

        self.y += (
            v *
            np.sin(self.theta) *
            dt
        )

        now = self.get_clock().now().to_msg()

        # ============================================================
        # 1. IMU
        # ============================================================

        imu_msg = Imu()

        imu_msg.header.stamp = now
        imu_msg.header.frame_id = 'imu_link'

        imu_msg.linear_acceleration.x = (
            np.random.normal(0, 0.05)
        )

        imu_msg.angular_velocity.z = (
            w +
            np.random.normal(0, 0.01)
        )

        self.imu_pub.publish(imu_msg)

        # ============================================================
        # 2. WHEEL ODOMETRY
        # ============================================================

        odom_msg = Odometry()

        odom_msg.header.stamp = now
        odom_msg.header.frame_id = 'odom'

        odom_msg.twist.twist.linear.x = (
            v +
            np.random.normal(0, 0.02)
        )

        odom_msg.twist.twist.angular.z = (
            w +
            np.random.normal(0, 0.01)
        )

        self.odom_pub.publish(odom_msg)

        # ============================================================
        # FAILURE SCENARIO
        #
        # 0 - 15 sec   : NORMAL
        # 15 - 25 sec  : GNSS ANOMALY
        # 25 - 45 sec  : GNSS OUTAGE / TUNNEL
        # 45 - 60 sec  : NORMAL RECOVERY
        # ============================================================

        cycle = elapsed % 60.0

        is_gnss_anomaly = (
            15.0 <= cycle < 25.0
        )

        is_tunnel = (
            25.0 <= cycle < 45.0
        )

        # ============================================================
        # NORMAL / ANOMALY GNSS
        # ============================================================

        if not is_tunnel:

            gps_msg = NavSatFix()

            gps_msg.header.stamp = now
            gps_msg.header.frame_id = 'gps_link'

            # --------------------------------------------------------
            # Normal GPS position
            # --------------------------------------------------------

            gps_lat = (
                self.lat_origin
                +
                (
                    self.y /
                    111111.0
                )
                +
                np.random.normal(
                    0,
                    0.00001
                )
            )

            gps_lon = (
                self.lon_origin
                +
                (
                    self.x /
                    (
                        111111.0 *
                        np.cos(
                            np.radians(
                                self.lat_origin
                            )
                        )
                    )
                )
                +
                np.random.normal(
                    0,
                    0.00001
                )
            )

            # ========================================================
            # 🚨 GNSS FAILURE INJECTION
            # ========================================================

            if is_gnss_anomaly:

                # Inject a large but plausible-looking position jump.
                #
                # Approximately 40 metres east and 30 metres north.
                #
                # The vehicle itself has NOT moved there.
                # This simulates a GNSS spoof/outlier event.

                gps_lat += 30.0 / 111111.0

                gps_lon += (
                    40.0 /
                    (
                        111111.0 *
                        np.cos(
                            np.radians(
                                self.lat_origin
                            )
                        )
                    )
                )

                self.get_logger().warn(
                    '[GNSS ATTACK] '
                    'Injecting false GPS position!',
                    throttle_duration_sec=3.0
                )

            else:

                self.get_logger().info(
                    '[GNSS NORMAL] '
                    f'Lat={gps_lat:.5f}, '
                    f'Lon={gps_lon:.5f}',
                    throttle_duration_sec=5.0
                )

            gps_msg.latitude = gps_lat
            gps_msg.longitude = gps_lon

            gps_msg.altitude = 0.0

            gps_msg.status.status = 0

            self.gps_pub.publish(gps_msg)

        # ============================================================
        # TUNNEL / GNSS OUTAGE
        # ============================================================

        else:

            self.get_logger().warn(
                '[TUNNEL DETECTED] '
                'GNSS Signal Lost! '
                'Relying on IMU + Odom',
                throttle_duration_sec=3.0
            )


# ====================================================================
# MAIN
# ====================================================================

def main(args=None):

    rclpy.init(args=args)

    node = NaviFusionSensorSimulator()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':

    main()
