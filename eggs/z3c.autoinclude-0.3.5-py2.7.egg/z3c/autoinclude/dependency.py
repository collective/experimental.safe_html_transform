import os
import logging
from zope.dottedname.resolve import resolve
from pkg_resources import resource_exists
from pkg_resources import get_provider
from pkg_resources import get_distribution
from z3c.autoinclude.utils import DistributionManager
from z3c.autoinclude.utils import ZCMLInfo

class DependencyFinder(DistributionManager):

    def includableInfo(self, zcml_to_look_for):
        """Return the packages in the dependencies which are includable.

        zcml_to_look_for - a list of zcml filenames we are looking for

        Returns a dictionary with the include candidates as keys, and lists
        of dotted names of packages that contain the include candidates as
        values.
        """
        result = ZCMLInfo(zcml_to_look_for)
        for req in self.context.requires():
            dist_manager = DistributionManager(get_provider(req))
            for dotted_name in dist_manager.dottedNames():
                try:
                    module = resolve(dotted_name)
                except ImportError, exc:
                    logging.getLogger("z3c.autoinclude").warn(
                        "resolve(%r) raised import error: %s" % (dotted_name, exc))
                    continue
                for candidate in zcml_to_look_for:
                    candidate_path = os.path.join(
                        os.path.dirname(module.__file__), candidate)
                    if os.path.isfile(candidate_path):
                        result[candidate].append(dotted_name)
        return result

def package_includes(project_name, zcml_filenames=None):
    """
    Convenience function for finding zcml to load from requirements for
    a given project. Takes a project name. DistributionNotFound errors
    will be raised for uninstalled projects.
    """
    if zcml_filenames is None:
        zcml_filenames = ['meta.zcml', 'configure.zcml', 'overrides.zcml']
    dist = get_distribution(project_name)
    include_finder = DependencyFinder(dist)
    return include_finder.includableInfo(zcml_filenames)
