Run: pip install -r requirements.txt
python main.py
Open training.ui in Qt Designer.
External train_cf.py and train_lstm.py are required for actual training. Output protocol: PROGRESS percent; LOSS horizon epoch loss val_loss; PRED horizon actual predicted; CF_RESULT horizon threshold precision recall f1; LSTM_RESULT horizon mae rmse r2.
