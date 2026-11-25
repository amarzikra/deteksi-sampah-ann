import json
import os
from pathlib import Path

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "train"
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "model_ann.keras"
HISTORY_PATH = MODEL_DIR / "history.json"

IMG_HEIGHT = 128
IMG_WIDTH = 128
BATCH_SIZE = 32
EPOCHS = int(os.environ.get("ANN_EPOCHS", "20"))
SEED = 42
CLASSES = ["Organic_Waste", "Plastics", "Carton", "Paper_and_Cardboard", "Aluminium"]


def buat_generator(subset):
    datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split=0.2
    )
    return datagen.flow_from_directory(
        DATA_DIR,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        classes=CLASSES,
        subset=subset,
        seed=SEED,
        shuffle=(subset == "training")
    )


def buat_model():
    model = tf.keras.models.Sequential([
        tf.keras.layers.Flatten(input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(len(CLASSES), activation="softmax")
    ])
    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model


def main():
    if not DATA_DIR.exists():
        raise SystemExit(f"Folder dataset tidak ditemukan: {DATA_DIR}")
    MODEL_DIR.mkdir(exist_ok=True)

    print("=== Memuat Dataset Citra Digital ===")
    train_generator = buat_generator("training")
    val_generator = buat_generator("validation")
    print(f"Jumlah data training: {train_generator.samples}")
    print(f"Jumlah data validasi: {val_generator.samples}")

    model = buat_model()
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=5,
            restore_best_weights=True
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(MODEL_PATH),
            monitor="val_accuracy",
            save_best_only=True
        )
    ]

    print("=== Melatih Model ANN ===")
    history = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=EPOCHS,
        callbacks=callbacks
    )

    loss, accuracy = model.evaluate(val_generator)
    model.save(str(MODEL_PATH))

    history_dict = {
        key: [float(value) for value in values]
        for key, values in history.history.items()
    }
    HISTORY_PATH.write_text(json.dumps(history_dict, indent=2), encoding="utf-8")

    print(f"Akurasi validasi: {accuracy:.4f}")
    print(f"Model tersimpan di: {MODEL_PATH}")
    print(f"Riwayat training tersimpan di: {HISTORY_PATH}")


if __name__ == "__main__":
    main()
