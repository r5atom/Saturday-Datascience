#!/bin/bash
set -ex

if [ -e "./assets/status.txt" ]
then
    mv -v --backup=numbered ./assets/status.txt ./assets/status-bup.txt
fi

python3 assets/auction_urls.py -v $1 $2 \
--config_file "assets/drz-settings.ini" \
--output_file "assets/source-$1.csv"
exit_code=$?

if [ $exit_code -gt 0 ]
then
  echo "stop script $0 with error: $exit_code"
  exit $exit_code
else
  echo "Continue"
fi

if [ "$2" = "O" ]
then
  dest_dir=~/data/satdatsci-images/opbod
else
  dest_dir=~/data/satdatsci-images
fi

python3 assets/download_photos.py -v \
--config_file "assets/drz-settings.ini" \
--input_file "assets/source-$1.csv" \
--output_file "assets/image-$1.csv" \
--destination_directory $dest_dir
exit_code=$?

if [ $exit_code -gt 0 ]
then
  echo "stop script $0 with error: $exit_code"
  exit $exit_code
else
  echo "Continue"
fi

python3 assets/main.py -v \
--input_file "assets/source-$1.csv" \
--config_file "assets/drz-settings.ini"
exit_code=$?

if [ $exit_code -gt 0 ]
then
  echo "stop script $0 with error: $exit_code"
  exit $exit_code
else
  echo "Continue"
fi

python3 assets/make_auction_setting_file.py $1 $2 $3 -v \
-c assets/drz-settings.ini \
-s assets/drz-settings-current.json
exit_code=$?

if [ $exit_code -gt 0 ]
then
  echo "stop script $0 with error: $exit_code"
  exit $exit_code
else
  echo "Continue"
fi

cat assets/drz-settings-current.json

cd 00-scrape
python3 ./scrape-drz-auction-results.py
python3 ./download-images.py
python3 ./add-rdw-info-to-drz.py
