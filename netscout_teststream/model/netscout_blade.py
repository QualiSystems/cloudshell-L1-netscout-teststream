import re

from cloudshell.layer_one.core.response.resource_info.entities.blade import Blade


class NetscoutBlade(Blade):
    REGISTERED_MODELS = {
        r'o[-_\s]blade': 'O-Blade',
        r's[-_\s]blade': 'S-Blade',
        r's[-_\s]blade[-_\s]pro': 'S-Blade-Pro',
        r't[-_\s]blade': 'T-Blade',
        r't100[-_\s]blade': 'T100-Blade',
        r'hs[-_\s]bank': 'Hs-Bank'
    }

    def _associate_blade_model(self, model_name):
        for patt in self.REGISTERED_MODELS:
            if re.search(patt, model_name, flags=re.IGNORECASE):
                return self.REGISTERED_MODELS[patt]
        raise Exception(self.__class__.__name__, 'Blade model {} is not registered'.format(model_name))

    def __init__(self, resource_id, model_name):
        super(NetscoutBlade, self).__init__(resource_id, model_name=self._associate_blade_model(model_name))
