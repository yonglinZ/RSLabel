import logging
import os.path as osp
import yaml
__appname__ = 'RSLabel'
here = osp.dirname(osp.abspath(__file__))

def name():
    return "OpenStreetMap plugin"


def description():
    return "Viewer and editor for OpenStreetMap data"


def version():
    return "Version 0.1"


def icon():
    import resources_rc
    return ":/plugins/osm_plugin/images/osm_load.png"


def classFactory(iface):
    print('*classFactory, begin to load labelme plugin')
    from .Plugin import LabelmePlugin
    # return object of our plugin with reference to QGIS interface as the only argument
    return LabelmePlugin(iface) 



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('RSLabel')
del logging

print('__init__ in labelme')

def versionNumber():
    return "0.1"


def get_default_config():
    config_file = osp.join(here, 'default_config.yaml')
    with open(config_file) as f:
        config = yaml.load(f)

    # save default config to ~/.labelmerc
    user_config_file = osp.join(osp.expanduser('~'), '.labelmerc')
    if not osp.exists(user_config_file):
        try:
            shutil.copy(config_file, user_config_file)
        except Exception:
            print('Failed to save config: {}'.format(user_config_file))

    return config


def validate_config_item(key, value):
    if key == 'validate_label' and value not in [None, 'exact', 'instance']:
        raise ValueError('Unexpected value `{}` for key `{}`'
                         .format(value, key))


def get_config(config_from_args=None, config_file=None):
    # Configuration load order:
    #
    #   1. default config (lowest priority)
    #   2. config file passed by command line argument or ~/.labelmerc
    #   3. command line argument (highest priority)

    # 1. default config
    config = get_default_config()

    # 2. config from yaml file
    if config_file is not None and osp.exists(config_file):
        with open(config_file) as f:
            user_config = yaml.load(f) or {}
        update_dict(config, user_config, validate_item=validate_config_item)

    # 3. command line argument
    if config_from_args is not None:
        update_dict(config, config_from_args,
                    validate_item=validate_config_item)

    return config
