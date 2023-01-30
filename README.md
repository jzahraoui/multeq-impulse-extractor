# multeq-impulse-extractor

creates rew impulse txt files from multeq ady file

## How to install multeq-impulse-extractor

* Install it using pip (recommended):

```bash
pip install git+https://github.com/jzahraoui/multeq-impulse-extractor.git
```

make sure $HOME/.local/bin/ is in your $PATH variable.

* Clone the repository and install it using the following command (Python3 and pip needed):

```bash
sudo python3 setup.py install --record files.txt
```

## use

export your MultEQ ady to your local directory.

then simply run the command :

```bash
multeq-impulse-extractor [your-file.ady]
```

the generated files can be directly used by REW

## uninstall

```bash
pip uninstall multeq-impulse-extractor
```

or if you didn't use pip:

```bash
sudo xargs rm -rf < files.txt
```
