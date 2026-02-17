# ChronoGeoCal repository


Just for the first time. Please create a virtual environment and install required libraries.

1. create a folder inside your home folder. 
```
mkdir ~/myenv
python3 -m venv ~/myenv
source ~/myenv/bin/activate
pip3 install -r requirements.txt

```

1.  `cd ~/ChronoGeoCal`
1.  `source ~/myenv/bin/activate`
1.  To generate prompts --
        `./run_all_prompts.sh ` This will run generate all the prompt files. Watch the output closely to see of ther are any failures.
1.  To run inference on prompt files you should run --
    ```./infer_all_prompts.sh```
    In order to run this you will have to update `endpoint_dict` in `evaluate_prompts.py` with model endpoints.

1.  To populate accuracy in JSON -
    ```./populate_accuracy.sh ```

Similar scripts exist for CoT prompts as well.


