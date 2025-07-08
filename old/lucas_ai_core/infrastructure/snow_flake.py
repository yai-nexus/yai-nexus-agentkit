import time


class Snowflake:
    """
    雪花算法ID生成器

    Args:
        worker_id (int): 工作机器ID (0-31)
        datacenter_id (int): 数据中心ID (0-31)
        sequence (int, optional): 起始序列号. 默认为 0
    """

    def __init__(self, worker_id: int, datacenter_id: int, sequence: int = 0):
        self.worker_id = worker_id  # 用于标识不同的工作机器
        self.datacenter_id = datacenter_id  # 用于标识不同的数据中心
        self.sequence = sequence  # 序列号，用于解决并发生成的 ID 冲突
        self.tw_epoch = 1288834974657  # Twitter Snowflake epoch (in milliseconds)，Snowflake 算法的起始时间点

        # Bit lengths，用于计算位数
        self.worker_id_bits = 5  # 5位，最大值为31
        self.datacenter_id_bits = 5  # 5位，最大值为31
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)  # 最大工作机器 ID
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_id_bits)  # 最大数据中心 ID
        self.sequence_bits = 12  # 12位，支持的最大序列号数
        self.sequence_mask = -1 ^ (
            -1 << self.sequence_bits
        )  # 序列号掩码，用于生成序列号

        # Create initial timestamp，初始化上一次生成 ID 的时间戳
        self.last_timestamp = self.current_timestamp()

        # Check worker_id and datacenter_id values，检查工作机器 ID 和数据中心 ID 的取值范围
        if self.worker_id > self.max_worker_id or self.worker_id < 0:
            raise ValueError(f"Worker ID must be between 0 and {self.max_worker_id}")
        if self.datacenter_id > self.max_datacenter_id or self.datacenter_id < 0:
            raise ValueError(
                f"Datacenter ID must be between 0 and {self.max_datacenter_id}"
            )

    @staticmethod
    def current_timestamp() -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)

    def generate(self) -> str:
        """
        生成一个唯一的雪花算法ID

        Returns:
            str: 16位的字符串ID

        Raises:
            ValueError: 当检测到时钟回拨时抛出
        """
        timestamp = self.current_timestamp()

        if timestamp < self.last_timestamp:
            raise ValueError(
                f"Clock moved backwards. Refusing to generate ID for {self.last_timestamp - timestamp} milliseconds"
            )

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & self.sequence_mask
            if self.sequence == 0:
                timestamp = self.wait_next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        # Generate Snowflake ID
        _id = (
            (
                (timestamp - self.tw_epoch)
                << (self.worker_id_bits + self.datacenter_id_bits)
            )
            | (self.datacenter_id << self.worker_id_bits)
            | self.worker_id << self.sequence_bits
            | self.sequence
        )
        return f"{_id:016d}"

    def wait_next_millis(self, last_timestamp: int) -> int:
        """
        等待下一个毫秒

        Args:
            last_timestamp (int): 上一次生成ID的时间戳

        Returns:
            int: 下一毫秒的时间戳
        """
        timestamp = self.current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self.current_timestamp()
        return timestamp
