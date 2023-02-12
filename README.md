# multeq-impulse-extractor

- creates REW compatible impulse txt files from multeq ady file
- create a new ady file with perfect speakers response for all mesurement positions.
  - level set to 0db
  - distance set to 3m
  - speaker type set to large
  - midrange compensation off
- import REW format txt mesurement files to custom target curves, this files must be placed in a folder named "filter" and must be named by multeq chanel name (ex. C.txt  FL.txt  FR.txt  SBL.txt  SBR.txt  SLA.txt  SRA.txt  SW1.txt  TFL.txt  TFR.txt  TRL.txt  TRR.txt)

## How to install multeq-impulse-extractor

- Install it using pip (recommended):

```bash
pip install git+https://github.com/jzahraoui/multeq-impulse-extractor.git
```

make sure $HOME/.local/bin/ is in your $PATH variable.

- Clone the repository and install it using the following command (Python3 and pip needed):

```bash
python3 -m build
pip install dist/multeq_impulse_extractor-1.0.5-py3-none-any.whl
```

## use

export your MultEQ mesurment from the mobile application to your local directory.

then simply run the command :

```bash
usage: extract.py [-h] -i INPUT [-o OUTPUT] [-d] [-c] [-f FILTER] [-e]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path to ady file
  -o OUTPUT, --output OUTPUT
                        Path to output result file, if not specified will use .result.ady extention. WARNING: it will be overwrited
  -d, --default         set default values : - 0db level - distance set to 3m - speaker type set to large - midrange compensation off
  -c, --clean           Output a file with cleaned response data
  -f FILTER, --filter FILTER
                        specify folder where resides your filters files. process will put them into custum target curve related chanels
  -e, --extract         Decode one channel at a time
```

the extract txt files can be directly imported to REW
the result ady file can be imported to the mobile application

## uninstall

```bash
pip uninstall multeq-impulse-extractor
```
