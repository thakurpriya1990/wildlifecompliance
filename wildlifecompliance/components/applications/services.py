import sys
import abc


def get_specie(species_list):
    requested_species = []

    tsc_service = TSCSpecieService(TSCSpecieCall)
    # tsc_service.set_strategy(TSCSpecieRecursiveCall)

    for specie in species_list:
        details = []
        details = tsc_service.search_taxon(specie)
        requested_species.append(details)

    return requested_species


class TSCSpecieService():
    """
    Interface for Threatened Species Communities api services.
    """
    def __init__(self, call_strategy):
        self._strategy = call_strategy

    def set_strategy(self, call_strategy):
        self._strategy = call_strategy

    def get_strategy(self):
        return self._strategy

    def search_taxon(self, specie_id):
        """
        Search taxonomy for species.
        """
        try:

            return self._strategy.request_species([specie_id])

        except BaseException:
            print "{} error: {}".format(self._strategy, sys.exc_info()[0])
            raise

    def __str__(self):
        return 'TSCSpecieService: {}'.format(self._strategy)


class TSCSpecieCallStrategy(object):
    """
    A Strategy Interface declaring a common operation for the TSCSpecie Call.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def request_species(self, species):
        """
        Operation for consuming TSCSpecie details.
        """
        pass


class TSCSpecieCall(TSCSpecieCallStrategy):
    """
    A TSCSpecie Call.
    """

    def __init__(self):
        self._depth = sys.getrecursionlimit()

    def set_depth(self, depth):
        """
        Set the number of recursion levels.
        """
        self._depth = depth if depth > 0 else sys.getrecursionlimit()

    def request_species(self, species):

        def send_request(species):
            pass

        return self.send_request(species)


class TSCSpecieRecursiveCall(TSCSpecieCallStrategy):
    """
    A Recursive strategy for the TSCSpecie Call.
    """

    def __init__(self):
        self._depth = sys.getrecursionlimit()

    def set_depth(self, depth):
        """
        Set the number of recursion levels.
        """
        self._depth = depth if depth > 0 else sys.getrecursionlimit()

    def request_species(self, species):
        LEVEL = 0
        return self.get_level_species(LEVEL, species)

    def get_level_species(self, level_no, level_species):
        requested_species = []

        def send_request_for_children(species):
            pass

        def send_request_for_parent(species):
            pass

        level_no = level_no + 1
        for level in range(level_no, self._depth):  # stopping rule.
            species = self.send_request_for_children(level_species)
            requested_species += species

            if species:
                next_level_species = self.get_level_species(level, species)
                for specie in next_level_species:
                    requested_species.append(specie)
            else:
                # retrieve name details for specie
                species = self.send_request_for_parent(level_species)
                requested_species = [species]
                break

        return requested_species

    def __str__(self):
        return 'Recursive call with max depth {}'.format(self.depth)


class TSCSpecie(object):

    __metaclass__ = abc.ABCMeta

    def get_parent(self):
        return self._parent

    def set_parent(self, parent):
        self._parent = parent

    def name(self):
        return self._name

    def add(self, root):
        pass

    def remove(self, root):
        pass

    def is_child(self):
        return False

    def get_children(self):
        return []

    @abc.abstractmethod
    def operation(self):
        pass


class ChildSpecie(TSCSpecie):
    """
    The child class represents the end objects of a TSCSpecie composition. A
    child cannot have any children.
    """

    def is_child(self):
        return True

    def operation(self):
        return "child"


class ParentSpecie(TSCSpecie):
    """
    The parent class represents the complex objects of a TSCSpecie composition
    that have children. These objects will delegate the work to the children.
    """

    def __init__(self):
        self._children = []

    def add(self, specie):
        self._children.append(specie)
        specie.set_parent(self)

    def remove(self, specie):
        self._children.remove(specie)
        specie.set_parent(None)

    def is_child(self):
        return False

    def get_children(self):
        return []

    def operation(self):
        """
        The parent will traverse recursively through all its children. A
        composite will pass the operation to its children until the whole tree
        has been traversed.
        """
        results = []
        for child in self._children:
            results.append(child.operation())

        return "Branch( {} ".format(results)
