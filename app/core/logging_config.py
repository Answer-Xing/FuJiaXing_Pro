"""structlog 日志配置——结构化日志输出"""
import structlog
import logging


def setup_logging(level: str = "INFO", is_development: bool = True):
    """配置结构化日志"""

    # 配置底层标准库
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
    )

    # 配置 structlog
    processors = [
        structlog.stdlib.add_log_level,  # 添加日志级别
        structlog.stdlib.add_logger_name,  # 添加 logger 名
        structlog.processors.TimeStamper(fmt="iso"),  # 时间戳
        structlog.processors.format_exc_info,  # 异常信息格式化
    ]

    if is_development:
        # 开发环境：人类友好的彩色输出
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # 生产环境：JSON 格式，方便日志采集系统处理
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
