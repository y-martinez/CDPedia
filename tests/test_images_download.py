# Copyright 2021 CDPedistas (see AUTHORS.txt)
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# For further info, check  https://github.com/PyAr/CDPedia/

import shutil
from unittest.mock import patch

from src.images.download import optimize_png, download, FetchingError

import pytest


@pytest.fixture
def image_config(tmp_path):
    def f(name):
        img_test_name = 'tests/fixtures/image_to_optimize.png'
        test_path = tmp_path / name
        shutil.copy(img_test_name, str(test_path))
        init_size = test_path.stat().st_size
        return test_path, init_size
    yield f


@pytest.mark.parametrize('filename', [
    'image.png',  # simple
    'Image.PNG',  # uppercase
    'moño.png',  # unicode
    'the image.png',  # spaces
])
def test_pngquant_optimize(image_config, filename):
    img_path, init_size = image_config(filename)
    optimize_png(str(img_path), init_size, init_size)
    final_size = img_path.stat().st_size
    assert init_size > final_size


def test_download_ok(tmp_path):
    test_path = tmp_path / 'foo' / 'bar' / 'baz.png'

    with patch('src.images.download.optimize_image') as _optimize_mock:
        with patch('src.images.download._download') as _download_mock:
            # real download will be ok, no need to patch RETRIES
            _download_mock.return_value = None

            download(('test-url', str(test_path)))

    # check directory were prepared ok
    assert test_path.parent.exists()

    # download and optimization was called ok
    _download_mock.assert_called_once_with('test-url', str(test_path))
    _optimize_mock.assert_called_once_with(str(test_path))


@pytest.mark.parametrize('extension', [
    '.svg',
    '.gif',
    '.Svg',
    '.Gif',
    '.SVG',
    '.GIF',
])
def test_download_no_optimization(extension, tmp_path):
    test_path = tmp_path / 'foo' / 'bar' / ('baz.' + extension)

    with patch('src.images.download.optimize_image') as _optimize_mock:
        with patch('src.images.download._download') as _download_mock:
            # real download will be ok, no need to patch RETRIES
            _download_mock.return_value = None

            download(('test-url', str(test_path)))

    # optimization was NOT called
    _optimize_mock.assert_not_called()


def test_download_retry_ok(tmp_path):
    test_path = tmp_path / 'foo' / 'bar' / 'baz.png'

    with patch('src.images.download.optimize_image'):
        with patch('src.images.download._download') as _download_mock:
            with patch('src.images.download.RETRIES', [0]):
                # first time ends with error, second ok
                _download_mock.side_effect = [
                    ValueError('pumba'),
                    None,
                ]
                download(('test-url', str(test_path)))

    # check directory were prepared ok
    assert test_path.parent.exists()

    # download was called twice
    assert _download_mock.call_count == 2


def test_download_problems(tmp_path):
    test_path = tmp_path / 'foo' / 'bar' / 'baz.png'

    with patch('src.images.download.optimize_image'):
        with patch('src.images.download._download') as _download_mock:
            with patch('src.images.download.RETRIES', [0]):
                # always in error
                _download_mock.side_effect = [
                    ValueError('pumba'),
                    ValueError('pumba'),
                ]
                with pytest.raises(FetchingError):
                    download(('test-url', str(test_path)))

    # check directory were prepared ok
    assert test_path.parent.exists()

    # download was called twice
    assert _download_mock.call_count == 2