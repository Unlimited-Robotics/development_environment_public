import rclpy
from rclpy.node import Node

from raya_status_msgs.msg import ComponentsStatus


NODE_NAMESPACE = '/developer'
NODE_NAME = 'components_status_subscriber'
STATUS_TOPIC_NAME = '/gary/status/all_components_status'

STATUS_DICT = {
    0: 'NOT_PRESENT',
    1: 'INITIALIZING',
    2: 'IDLE',
    3: 'RUNNING',
    4: 'BUSY',
    5: 'WARNING',
    6: 'RECOVERY',
    7: 'ERROR',
    8: 'CRITICAL',
    9: 'EMERGENCY',
}


class ComponentsStatusSubscriber:

    def __init__(self):
        self.node = Node(
            node_name=NODE_NAME,
            namespace=NODE_NAMESPACE,
        )
        self.subscription = self.node.create_subscription(
            msg_type=ComponentsStatus,
            topic=STATUS_TOPIC_NAME,
            callback=self.listener_callback,
            qos_profile=10,
        )
        self.logger = self.node.get_logger()
        self.subscription  # prevent unused variable warning


    def listener_callback(self, msg):
        self.logger.info('Components status received:')
        for component_status in msg.components_status:
            name = component_status.component_name
            status = STATUS_DICT[component_status.status]
            self.logger.info(f'  - {name}: {status}')
        self.logger.info('')


    def run(self):
        rclpy.spin(self.node)
        self.node.destroy_node()


def main(args=None):
    rclpy.init(args=args)
    minimal_subscriber = ComponentsStatusSubscriber()
    minimal_subscriber.run()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
