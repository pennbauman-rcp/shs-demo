#!/bin/sh


if [ -z "$(command -v org.inkscape.Inkscape)" ]; then
	echo "Missing org.inkscape.Inkscape"
fi

for f in $(find . -regextype egrep -regex '\./[a-z]+_[0-9a-f]{6}\.svg'); do
	f_start="$(echo "$f" | sed 's/\.svg//')"
	for n in 10 20 40 80; do
		png_file="${f_start}_${n}x${n}.png"
		echo $png_file
		org.inkscape.Inkscape -w $n -h $n "$f" --export-filename "$png_file"
	done
done

# 
