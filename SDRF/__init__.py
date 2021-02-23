import pandas as pd
import re
from collections import OrderedDict
from enum import Enum


class TypeOfSDRFCol(Enum):
    """
    TypeSDRFCol enumerator holds the structure of fields and subfields allowed in an SDRF file
    """

    COMMENT = 'Comment', []
    TERM_ACCESSION_NUMBER = 'Term Accession Number', [], False
    TERM_SOURCE_REF = 'Term Source REF', [TERM_ACCESSION_NUMBER], False
    DESCRIPTION = 'Description', [], False
    UNIT = 'Unit', [TERM_SOURCE_REF], False
    PARAMETER_VALUE = 'Parameter Value', [UNIT, COMMENT, TERM_SOURCE_REF], False
    DATE = 'Date', [], False
    PERFORMER = 'Performer', [COMMENT], False
    FACTOR_VALUE = 'Factor Value', [UNIT, TERM_SOURCE_REF], True
    LABEL = 'Label', [TERM_SOURCE_REF], False
    TECHNOLOGY_TYPE = 'Technology Type', [TERM_SOURCE_REF], False
    ARRAY_DESIGN_FILE = 'Array Design File', [TERM_SOURCE_REF, COMMENT], False
    ARRAY_DESIGN_REF = 'Array Design REF', [TERM_SOURCE_REF, COMMENT], False
    MATERIAL_TYPE = 'Material Type', [TERM_SOURCE_REF], False
    PROVIDER = 'Provider', [COMMENT], False
    CHARACTERISTICS = 'Characteristics', [UNIT, TERM_SOURCE_REF], False

    PROTOCOL_REF = 'Protocol Ref', [TERM_SOURCE_REF, PARAMETER_VALUE, PERFORMER, DATE, COMMENT], True
    IMAGE_FILE = 'Image file', [COMMENT], True
    DERIVED_ARRAY_DATA_MATRIX_FILE = 'Derived Array Data Matrix File', [COMMENT], True
    ARRAY_DATA_MATRIX_FILE = 'Array Data Matrix File', [COMMENT], True
    DERIVED_ARRAY_DATA_FILE = 'Derived Array Data File', [COMMENT], True
    ARRAY_DATA_FILE = 'Array Data File', [COMMENT], True
    NORMALIZATION_NAME = 'Normalization Name', [COMMENT], True
    SCAN_NAME = 'Scan Name', [COMMENT], True
    ASSAY_NAME = 'Assay Name', [TECHNOLOGY_TYPE, ARRAY_DESIGN_FILE, ARRAY_DESIGN_REF, COMMENT], True
    LABELED_EXTRACT_NAME = 'Labeled Extract Name', [CHARACTERISTICS, MATERIAL_TYPE, DESCRIPTION, LABEL, COMMENT], True
    EXTRACT_NAME = 'Extract Name', [CHARACTERISTICS, MATERIAL_TYPE, DESCRIPTION, COMMENT], True
    SAMPLE_NAME = 'Sample Name', [CHARACTERISTICS, MATERIAL_TYPE, DESCRIPTION, COMMENT], True
    SOURCE_NAME = 'Source Name', [CHARACTERISTICS, PROVIDER, MATERIAL_TYPE, DESCRIPTION, COMMENT], True

    def __init__(self, name, subfields: list, is_node: bool=False):
        self._label = name
        # subfields inside the constructur become tuples for some reason.
        self._subfields = [x[0] for x in subfields]
        self._is_node = is_node
        self._label_for_compare = name.lower().replace(" ", "")

    def has_subfield(self, subfield):
        return subfield in self._subfields

    @staticmethod
    def get_type(label: str):
        label = re.sub("\[.*$", "", label)
        for type in TypeOfSDRFCol:
            if label.lower().replace(" ", "") == type.label_for_compare:
                return type

    @property
    def is_node(self):
        return self._is_node

    @property
    def label(self):
        return self._label

    @property
    def label_for_compare(self):
        return self._label_for_compare


"""
Represents either a characteristic, a factor or a comment, which can in turn
have sub fields
"""


def add_to_dict(dict, ext_dic, ext_key, new_key):
    """
    Recursive method to add elements to a dictionary with conflicting keys.
    :param dict:
    :param ext_dic:
    :param key:
    :return:
    """
    if new_key in dict:
        add_to_dict(dict, ext_dic, ext_key, new_key +"_")
    else:
        dict[new_key] = ext_dic[ext_key]


class SDRFColumn(object):
    """
    Holds columns of an SDRF file, considering the idea that fields in SDRF have distinct types (TypeOfSDRFCol) and
    can have subfields (columns to its right that characterise it). Comparisons are done considering this, so it
    caters for the fact that SDRFs many times have columns repeated with the same name (but that are subfields of
    different fields).

    characteristic_organism = SDRFNamedEntityAttribute(type='characteristic', name='organism', data=sdrf['Characteristic[organism]'])
    """

    def __init__(self, name, data: pd.Series, type: TypeOfSDRFCol, index: int=0):
        """
        Initialises an SDRFColumn with a name, data (pandas series) and a type, and creates provisions for
        storing its subfields, which can be added once the object exists.

        :param name: The name of the column as written in the SDRF. It is meant to be used with the pandas column name,
        and it will remove any suffixes for duplicated columns.
        :param data: The pandas series containing its data.
        :param type: The type of the column
        """
        self.type = type
        # remove .1, .2 added by Pandas for repeated column names
        self.name = SDRFColumn.remove_suffix(name)
        self.column_data = data
        self.fields = list()
        self.index = index

    def __eq__(self, other):
        """
        Comparison is based on the type and name of the column, and for the name it considers that spaces and
        capitalisation doesn't matter, as stated in the MAGETab specs.

        :param other:
        :return: true if equals based on above criteria.
        """
        if isinstance(other, SDRFColumn) and other.type == self.type \
                and self.index == other.index:
            return SDRFColumn.format_for_comp(self.name) == SDRFColumn.format_for_comp(other.name)
        return False

    def size(self):
        """
        The size of the column, based on the size of the underlying panda series.

        :return: integer for the size
        """
        return self.column_data.size

    @staticmethod
    def remove_suffix(col_name):
        match = re.search('(.*?)(\.\d+){,1}$', col_name)
        return match.group(1)

    @staticmethod
    def format_for_comp(col_name):
        """
        Formats a string (lower, remove spaces) that is meant to be a column name to enable comparisons only.

        :param col_name:
        :return: col_name lowercase, no spaces.
        """
        return col_name.lower().replace(" ", "")

    def get_last_field_recursively(self):
        if self.fields:
            return self.fields[-1].get_last_field_recursively()
        else:
            return self

    def add_field(self, field, compute_index=False):
        """
        Adds a subfield to the column. A new field added will either belong to the field itself
        or to its last sub^n-field (the last field that it was added to it).

        TODO check logic here, might be wrong for the route merge_external-> not in self fields -> add_field
        :param field:
        :return:
        """
        # if not field.type:  # we only append
        #     self.fields.append(field)
        if self.fields:
            last_subfield = self.get_last_field_recursively()
            if last_subfield.type.has_subfield(field.type):
                if compute_index:
                    index = SDRFColumn.col_compute_index(field, last_subfield)
                    field.index = index
                # Assume that it should be added as a subfield of this fields
                # last added subfield if it is compatible with it.
                last_subfield.fields.append(field)
                return

        if compute_index:
            index = SDRFColumn.col_compute_index(field, self)
            field.index = index

        if self.type.has_subfield(field.type):
            print(f"WARNING: Adding {field.name} of type {field.type} to node {self.name}, "
                  f"which doesn't have that as subfield type")

        self.fields.append(field)


    @staticmethod
    def col_compute_index(new_field, prospective_parent_field):
        index = 0
        for sf in prospective_parent_field.fields:
            if SDRFColumn.format_for_comp(new_field.name) == SDRFColumn.format_for_comp(sf.name):
                index += 1
        return index

    def merge_external(self, outer):
        """
        Merges an external SDRFColumn outer into this same column, if they are considered equals.
        When merging, all subfields of the external are tried to merge to the subfields of this
        object.
        :param outer: the object to try to merge.
        :return: true if merged
        """
        if outer == self:
            # Note that the equals method for SDRFColumn is overridden
            # to depend only on the name and type of the column, not that
            # it is the same object in memory.
            original_size = self.column_data.size
            self.column_data = self.column_data.append(outer.column_data, ignore_index=True)

            for outer_field in outer.fields:
                if outer_field in self.fields:
                    # find the internal subfield where we need to do the merge.
                    field = self.fields[self.fields.index(outer_field)]
                    field.merge_external(outer_field)
                else:
                    # if the outer subfield is not part of this field's subfields
                    # the simply add it to the side, appending the original size at the start
                    outer_field.add_empty_rows(n=original_size, start=True, max_size=self.size())
                    self.add_field(outer_field)
            return True
        return False

    def complete_recursively_with_blanks_up_to(self, new_size):
        """
        This methods adds blanks at the end of the series to reach the new size stated.
        It will then execute recursively on each subfield when it does top up.

        :param new_size: new size that the series should have at the end
        :return:
        """
        if self.column_data.size < new_size:
            # if the current column is smaller, then add empty_rows at the end for this
            # and all its subfields (handled by add_empty_rows method). If this field
            # needs topping up, then all its subfields should need it, as no subfield could have been
            # added if the field wasn't.
            self.add_empty_rows(n=(new_size-self.column_data.size), start=False, max_size=new_size)
        elif self.column_data.size == new_size:
            # while the main field had rows added, many of its subfields might not have been
            for field in self.fields:
                field.complete_recursively_with_blanks_up_to(new_size)

    def add_empty_rows(self, n: int, start: bool, max_size=None):
        """
        Adds empty rows to the current named entity and all its sub fields

        :param n: Number of rows
        :param start: True for appending the rows to the beginning, false for adding them at the end.
        :return:
        """

        if max_size and max_size < self.column_data.size + n:
            print(f"Trying to add more rows than it should be for {self.name}... skipping")
        else:
            to_add = pd.Series([""]*n)
            if start:
                self.column_data = to_add.append(self.column_data, ignore_index=True)
            else:
                self.column_data = self.column_data.append(to_add, ignore_index=True)

        # if we are adding empty elements to the named entity, then all
        # its subfields (comments, characteristics, etc) need to have the same added
        for field in self.fields:
            field.add_empty_rows(n=n, start=start, max_size=max_size)

    def as_ordered_dict(self):
        """
        Stores the SDRF data as an ordered dictionary, so that column names don't clash. This is
        intended for the generation of a new pandas dataframe once the merging process at the level
        of columns is done.

        :return: order dictionary with all the data from the SDRFColumns representation.
        """
        dict = OrderedDict()
        columns = list()

        dict[self.name] = self.column_data
        columns.append(self.name)

        for field in self.fields:
            f_dict, f_columns = field.as_ordered_dict()
            for k in f_dict:
                add_to_dict(dict, f_dict, k, k)
            columns.extend(f_columns)

        return dict, columns

    def find_subfield_recursively(self, field_name):
        """
        Finds a subfield with this field name recursively

        :param field_name:
        :return:
        """

        if SDRFColumn.format_for_comp(self.name) == SDRFColumn.format_for_comp(field_name):
            return self
        for subfield in self.fields:
            sf = subfield.find_subfield_recursively(field_name)
            if sf:
                return sf
        return None


class SDRFEdgeColumn(SDRFColumn):
    """
    Edge columns are expected to be in between node columns. To identify them, the source and sink nodes
    surrounding the edge column become relevant. We keep track as well of the instance number within the SDRF.
    They otherwise behave like Nodes in every other respect.

    Edge columns are considered equivalent when they have the same source
    node (in principle, they should have the same source node at least and the same instance index)
    but there is only a single edge per source, so this should hold fine.
    """

    def __init__(self, name, data: pd.Series, type: TypeOfSDRFCol, source_node: SDRFColumn, index: int):
        SDRFColumn.__init__(self, name, data, type, index=index)
        self.source_node = source_node

    def __eq__(self, other):
        """
        Two edge nodes are considered equal if the have the same source node, the same type and
        instance index (in which position, among same name of edge column, they appear in the SDRF.
        :param other:
        :return:
        """
        if isinstance(other, SDRFEdgeColumn) \
                and other.type == self.type \
                and other.source_node == self.source_node \
                and other.index == self.index:
            return SDRFColumn.format_for_comp(self.name) == SDRFColumn.format_for_comp(other.name)
        return False


class SDRF(object):

    def __init__(self, path_to_sdrf):
        """

        :param path_to_sdrf:
        """
        self.table = pd.read_csv(path_to_sdrf, sep="\t")
        self.node_edges = list()
        self.nrows = len(self.table.index)

        # Change Hybridization Name to Assay Name
        self.__replace_old_column_names()

        for col in self.table.columns:
            col_no_suffix = SDRFColumn.remove_suffix(col)
            type_of_col = TypeOfSDRFCol.get_type(col_no_suffix)

            if type_of_col is None:
                print(f"WARNING {col} is not recognised as a valid column, skipping it!")
                continue
            if type_of_col == TypeOfSDRFCol.PROTOCOL_REF:
                # Edge nodes
                index = self.__index_for_protocol_ref(current_node)
                self.node_edges.append(SDRFEdgeColumn(col, self.table[col], type_of_col, current_node, index))
                current_ne = self.node_edges[-1]
                continue
            if type_of_col.is_node:
                # First level object
                # TODO move suffix logic handling inside SDRFColumn, as this is available from original col name.
                # actually ^^^ cannot be done, because subfields also need suffixes.
                index = self.__index_for_repeated_cols(col_no_suffix)
                self.node_edges.append(SDRFColumn(col, self.table[col], type_of_col, index=index))
                current_ne = self.node_edges[-1]
                current_node = self.node_edges[-1]
            else:
                # This is a subfield somewhere in the last addition
                field = SDRFColumn(name=col, data=self.table[col], type=type_of_col, index=0)
                current_ne.add_field(field, compute_index=True)

        self.col_size = len(self.node_edges)
        # TODO make sure that Comment[technical replicate group] is between Assay Name and Technology Type
        # TODO remove whitespaces in otherwise empty fields.
        self.__factor_values_to_the_end()

    def __index_for_repeated_cols(self, node_edge_name: str, parent_node: SDRFColumn=None):
        count = 0
        if parent_node:
            # a parent node is defined, so we search only within its subfields
            for sf in parent_node.fields:
                if SDRFColumn.format_for_comp(sf.name) == SDRFColumn.format_for_comp(node_edge_name):
                    count += 1
        else:
            for ne in self.node_edges:
                if SDRFColumn.format_for_comp(ne.name) == SDRFColumn.format_for_comp(node_edge_name):
                    count += 1
        return count


    def __index_for_protocol_ref(self, source_node: SDRFColumn):
        """
        Obtains the instance number or index for a Protocol Ref edge column (the only type of Edge columns?).
        :param source_node:
        :return:
        """
        count = 0
        for edge in [edge for edge in self.node_edges if edge.type == TypeOfSDRFCol.PROTOCOL_REF]:
            if edge.source_node == source_node:
                count += 1
        return count

    def get_size_for_column(self, node_name, subfield):
        """
        Returns size for specific node or node's subfield (if specified)

        :param node_name: for the first level node to get the size.
        :param subfield:
        :return:
        """
        for node in self.node_edges:
            if SDRFColumn.format_for_comp(node.name) == SDRFColumn.format_for_comp(node_name):
                if subfield:
                    for sf in node.fields:
                        if SDRFColumn.format_for_comp(sf.name) == SDRFColumn.format_for_comp(subfield):
                            return sf.size()
                else:
                    return node.size()

    def add_block_comment(self, node, comment_name, comment_value):
        """
        Adds a comment (titled as Comment[name]) to all the rows, to the given node name.

        Introduced originally to add Comment[Study] for merging purposes.

        :param node: Name of the node, needs to be present in the SDRF
        :param comment_name: Used to set the title to Comment['comment_name']
        :param comment_value: the value to use
        :return:
        """
        # Get node position
        if node in self.table.columns:
            col_number_node = self.table.columns.get_loc(node)+1
        else:
            ValueError(f"Node {node} is not a column in the table. Exiting.")
        # Add column to the table
        col_name = f'Comment[{comment_name}]'
        self.table.insert(col_number_node, col_name, comment_value)
        # Add column to the node_edges list as an SDRF column.
        comment_sdrf_col = SDRFColumn(name=col_name,
                                      data=self.table.iloc[:, col_number_node],
                                      type=TypeOfSDRFCol.COMMENT)
        for ne in self.node_edges:
            if ne.name == node:
                ne.add_field(comment_sdrf_col)

    def merge_external(self, external_sdrf):
        """
        Merges an external SDRF into the current one, by either appending downwards
        as new rows (when the column exists) or adding the new columns and empty rows. The operation
        is done per named entity, which in turn handles its own observations and so on.

        Changes are made on the calling SDRF.

        :param external_sdrf:
        :return:
        """
        for ext_ne in external_sdrf.node_edges:
            if ext_ne in self.node_edges:
                ne = self.node_edges[self.node_edges.index(ext_ne)]
                ne.merge_external(ext_ne)
            else:
                # in this case, new columns for the named entity and its subsidiary
                # elements need to be added, and the data from the external entity
                # needs to be subject to addition of empty rows at the beginning.
                ext_ne.add_empty_rows(self.nrows, start=True)
                if isinstance(ext_ne, SDRFEdgeColumn):
                    # For edge columns, they need to be added between the source node
                    # and then next node.
                    index_source_node = self.node_edges.index(ext_ne.source_node)
                    index_to_add = -1
                    for i in range(index_source_node+1, len(self.node_edges)):
                        if not isinstance(self.node_edges[i], SDRFEdgeColumn):
                            index_to_add = i
                            break
                    if index_to_add > 0:
                        self.node_edges.insert(index_to_add, ext_ne)
                        continue
                # for any other type, or if we are already at the end, simply append at the end.
                self.node_edges.append(ext_ne)
            if None in self.node_edges:
                print("WARNING empty element in node edges.")

        new_size = self.nrows + external_sdrf.nrows

        # Increase size of untouched series (nothing was added to them)
        for ne in self.node_edges:
            # This is currently checking that parent nodes, which might have had things added,
            # but they in turn could have have subfields to which nothing was added. So we need
            # to recursively check that all subfields have the new length
            ne.complete_recursively_with_blanks_up_to(new_size)

        # Make sure that all factor values are at the end.
        self.__factor_values_to_the_end()

        # TODO Make sure that technical replicates follow <study>-<group> pattern instead of just pattern

        # Append all elements into the a new table and replace the older one.
        data_for_pandas = OrderedDict()
        columns = list()
        for ne in self.node_edges:
            ne_dict, ne_cols = ne.as_ordered_dict()
            for k in ne_dict:
                add_to_dict(data_for_pandas, ne_dict, k, k)
            columns.extend(ne_cols)

        for k in data_for_pandas:
            data_for_pandas[k].reindex(copy=False)

        self.table = pd.DataFrame(data=data_for_pandas)
        self.table.columns = columns
        self.nrows = new_size

    def __factor_values_to_the_end(self):
        first_factor_index = None
        # TODO this should also modify the table order, but only pick the elements being moved here.
        for i in range(len(self.node_edges)):
            if first_factor_index is None and self.node_edges[i].type == TypeOfSDRFCol.FACTOR_VALUE:
                first_factor_index = i
                continue
            if first_factor_index and self.node_edges[i].type != TypeOfSDRFCol.FACTOR_VALUE:
                # A non-factor value after a factor value, move it
                l = self.node_edges
                l.insert(first_factor_index, l.pop(i))

    def __replace_old_column_names(self):
        # This could go eventually in a better place, but since it is only one currently...
        old_new = {'hybridizationname': 'Assay Name'}

        columns = self.table.columns.tolist()
        for col in columns:
            col_formatted = SDRFColumn.format_for_comp(col)
            if col_formatted in old_new:
                self.table.rename(columns={col: old_new[col_formatted]}, inplace=True)

    def prepend_into_column(self, node, comment_name, value, change_empty):
        """
        Prepends a string to a column, potentially inside a subfield if specified.
        :param node: Node where to exert the change
        :param comment_name: If the comment name is provided, change is done within this comment of the node.
        :param value: Value to prepend to all elements.
        :param change_empty: Whether to prepend as well to fields that are empty
        :return:
        """
        # Localise column where the change should be exerted
        node_obj = None
        for n in self.node_edges:
            if SDRFColumn.format_for_comp(n.name) == SDRFColumn.format_for_comp(node):
                if comment_name:
                    node_obj = n.find_subfield_recursively(field_name=f"Comment[{comment_name}]")
                else:
                    node_obj = n

        if not node_obj:
            if comment_name:
                print(
                    f"WARNING {node} node or node comment {comment_name} specified not found... "
                    f"skipping prepending value {value} to that node.")
            else:
                print(
                    f"WARNING {node} node specified not found... skipping prepending value {value} to than node.")
            return

        if change_empty:
            node_obj.column_data = value + "_" + node_obj.column_data
        else:
            # Do it for only not empty values.
            node_obj.column_data[node_obj.column_data.notna()] = value \
                                                                 + "_" + \
                                                                 node_obj.column_data[node_obj.column_data.notna()]












