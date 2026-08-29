from setuptools import find_packages, setup

package_name = 'navifusion_sim'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kshitiz',
    maintainer_email='kshitiz@todo.todo',
    description='NaviFusion Sensor Simulator and EKF Fusion Package',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'sensor_simulator = navifusion_sim.sensor_simulator:main',
            'ekf_fusion_node = navifusion_sim.ekf_fusion_node:main',
        ],
    },
)
