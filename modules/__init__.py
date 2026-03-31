"""
游戏管理模块包
统一管理所有游戏功能相关的管理器类
"""

from .ac_manager import ACChallengeManager, AutoClaimProgressManager
from .shenyuan_manager import ShenyuanManager
from .zh_manager import ZHManager
from .hd_dashang_manager import HDDashang
from .yl_manager import YLManager
from .wk_manager import WKManager
from .dy_manager import DYManager
from .da_manager import DAManager
from .rzsg_manager import RZSGManager
from .py_manager import PeiyuManager
from .kn_manager import KNManager
from .gem_team_manager import GemTeamManager
from .story_battle import StoryBattleManager
from .trade_manager import TradeManager
from .nuanchun_manager import NuanChunManager
from .guild_manager import GuildManager, GuildBatchManager
from .ghxs_manager import GHXSManager

__all__ = [
    'ACChallengeManager',
    'AutoClaimProgressManager',
    'ShenyuanManager',
    'ZHManager',
    'HDDashang',
    'YLManager',
    'WKManager',
    'DYManager',
    'DAManager',
    'RZSGManager',
    'PeiyuManager',
    'KNManager',
    'GemTeamManager',
    'StoryBattleManager',
    'TradeManager',
    'NuanChunManager',
    'GuildManager',
    'GuildBatchManager',
    'GHXSManager'
]

__version__ = '1.0.0'
__author__ = 'KPBL Game Tools'
__description__ = '游戏管理模块包 - 提供各种游戏功能的管理器类'