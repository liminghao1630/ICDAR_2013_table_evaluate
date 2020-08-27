import os
from xml.dom import minidom
import json
from pdf2image import convert_from_path
from tqdm import tqdm


if __name__ == '__main__':
    json_dir = r'D:\Company\Projects\ICDAR_2013_table_evaluate\prediction_results\icdar2013_table_epoch100'
    pdf_dir = r'D:\Company\Projects\ICDAR_2013_table_evaluate\icdar2013-competition-dataset-with-gt\pdf'
    result = json.load(open(os.path.join(json_dir, 'evaluate_result.json'), 'r'))
    img_size = json.load(open(r'D:\Company\Projects\ICDAR_2013_table_evaluate\img_size.json', 'r'))

    for pdf_file in tqdm(os.listdir(pdf_dir)):
        if not pdf_file.endswith('.pdf'):
            continue

        basename = pdf_file.replace('.pdf', '')
        if not os.path.exists(os.path.join(pdf_dir, basename + '_rate_cache.json')):
            big_ims = convert_from_path(os.path.join(pdf_dir, pdf_file))
            small_ims = convert_from_path(os.path.join(pdf_dir, pdf_file), dpi=72)

            rates = {}
            for page, (big_im, small_im) in enumerate(zip(big_ims, small_ims)):
                rates[str(page)] = (big_im.size[0] / small_im.size[0] + big_im.size[1] / small_im.size[1]) / 2

            json.dump(rates, open(os.path.join(pdf_dir, basename + '_rate_cache.json'), 'w'))
        else:
            rates = json.load(open(os.path.join(pdf_dir, basename + '_rate_cache.json'), 'r'))

        img_files = []
        for img_file in result.keys():
            if img_file.startswith(basename):
                img_files.append(img_file)

        root = minidom.Document()
        xml = root.createElement('document')
        xml.setAttribute('filename', pdf_file)
        root.appendChild(xml)

        table_id = 0

        for filename in sorted(img_files):
            im_width, im_height = img_size[filename]
            page = int(filename[filename.find('_') + 1: filename.rfind('_')])
            rate = rates[str(page)]
            page += 1

            for bbox in result[filename]:
                xmin, y0, xmax, y1 = bbox
                ymin = im_height - y1
                ymax = im_height - y0

                xmin, ymin, xmax, ymax = [int(v / rate) for v in [xmin, ymin, xmax, ymax]]

                table_id += 1
                table = root.createElement('table')
                table.setAttribute('id', str(table_id))

                region = root.createElement('region')
                region.setAttribute('id', '1')
                region.setAttribute('page', str(page))

                boundingbox = root.createElement('bounding-box')
                boundingbox.setAttribute('x1', str(xmin))
                boundingbox.setAttribute('y1', str(ymin))
                boundingbox.setAttribute('x2', str(xmax))
                boundingbox.setAttribute('y2', str(ymax))

                region.appendChild(boundingbox)
                table.appendChild(region)

                xml.appendChild(table)

        xml_str = root.toprettyxml(indent='\t')
        # print(xml_str)
        with open(os.path.join(json_dir, basename + '-reg-result.xml'), 'w') as fp:
            fp.write(xml_str)



