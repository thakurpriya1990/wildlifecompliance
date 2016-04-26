def create_data_from_form(form_structure, post_data, file_data, post_data_index=None):
    data = {}

    for item in form_structure:
        data.update(_create_data_from_item(item, post_data, file_data, post_data_index))

    return data


def _create_data_from_item(item, post_data, file_data, post_data_index=None):
    item_data = {}

    if 'name' in item and item.get('type', '') != 'group':
        if item.get('type', '') == 'declaration':
            if post_data_index is not None:
                post_data_list = post_data.getlist(item['name'])
                if len(post_data_list) > 0:
                    item_data[item['name']] = post_data_list[post_data_index]
                else:
                    item_data[item['name']] = False
            else:
                item_data[item['name']] = post_data.get(item['name'], 'off') == 'on'
        elif item.get('type', '') == 'file':
            if item['name'] in file_data:
                item_data[item['name']] = str(file_data.get(item['name']))
            elif item['name'] + '-existing' in post_data and len(post_data[item['name'] + '-existing']) > 0:
                    item_data[item['name']] = post_data.get(item['name'] + '-existing')
            else:
                item_data[item['name']] = ''
        else:
            post_data_list = post_data.getlist(item['name'])
            if post_data_index is not None and len(post_data_list) > 0:
                item_data[item['name']] = post_data_list[post_data_index]
            else:
                item_data[item['name']] = post_data.get(item['name'])

    if 'children' in item:
        if item.get('type', '') == 'group':
            # check how many groups there are
            num_groups = 0
            for group_item in item.get('children'):
                if group_item['type'] != 'section' and group_item['type'] != 'group':
                    num_groups = len(post_data.getlist(group_item['name']))
                    break

            groups = []
            for group_index in range(0, num_groups):
                group_data = {}
                for child in item['children']:
                    group_data.update(_create_data_from_item(child, post_data, file_data, group_index))
                groups.append(group_data)
            item_data[item['name']] = groups
        else:
            for child in item['children']:
                item_data.update(_create_data_from_item(child, post_data, file_data, post_data_index))

    return item_data


def get_all_filenames_from_application_data(item, data):
    filenames = []
    if item.get('type', '') == 'file':
        if item['name'] in data and len(data[item['name']]) > 0:
            filenames.append(data[item['name']])

    if 'children' in item:
        for child in item['children']:
            if child.get('type', '') == 'group':
                for child_data in data[child['name']]:
                    filenames += get_all_filenames_from_application_data(child, child_data)
            else:
                filenames += get_all_filenames_from_application_data(child, data)

    return filenames