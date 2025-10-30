/*
 * Medical Camera Controller - Arduino Code with NeoPixel Ring
 * Управление камерой через кнопку + светодиодное кольцо
 */

#include <Adafruit_NeoPixel.h>

// Пины
const int BUTTON_PIN = 3;
const int LED_RING_PIN = 6;

// Настройки светодиодного кольца
const int LED_COUNT = 8;          // 8 светодиодов в кольце
const int LED_BRIGHTNESS = 10;    // Яркость 10/255

// Переменные для обработки кнопки
int lastButtonState = HIGH;
unsigned long pressStartTime = 0;
const unsigned long DEBOUNCE_DELAY = 50;
const unsigned long LONG_PRESS_TIME = 1000;

bool longPressSent = false;
bool cameraActive = false;        // Состояние камеры

// Создаем объект для светодиодного кольца
Adafruit_NeoPixel ledRing = Adafruit_NeoPixel(LED_COUNT, LED_RING_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(9600);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Инициализация светодиодного кольца
  ledRing.begin();
  ledRing.setBrightness(LED_BRIGHTNESS);
  ledRing.show(); // Изначально все светодиоды выключены
  
  delay(2000);
  Serial.println("ARDUINO_READY");
}

void loop() {
  int currentButtonState = digitalRead(BUTTON_PIN);
  
  // Если состояние кнопки изменилось
  if (currentButtonState != lastButtonState) {
    delay(DEBOUNCE_DELAY);
    currentButtonState = digitalRead(BUTTON_PIN);
    
    if (currentButtonState != lastButtonState) {
      if (currentButtonState == LOW) {
        // Кнопка нажата - запоминаем время начала
        pressStartTime = millis();
        longPressSent = false;
      } else {
        // Кнопка отпущена - определяем тип нажатия
        unsigned long pressDuration = millis() - pressStartTime;
        
        if (pressDuration < LONG_PRESS_TIME && !longPressSent) {
          // Короткое нажатие - переключение камеры
          cameraActive = !cameraActive;  // Меняем состояние камеры
          Serial.println("SHORT_PRESS");
          
          // Обновляем светодиодное кольцо
          updateLedRing();
        }
      }
      lastButtonState = currentButtonState;
    }
  }
  
  // Проверяем длинное нажатие в процессе удержания кнопки
  if (currentButtonState == LOW && !longPressSent) {
    unsigned long pressDuration = millis() - pressStartTime;
    
    if (pressDuration >= LONG_PRESS_TIME) {
      // Длинное нажатие
      Serial.println("LONG_PRESS");
      longPressSent = true;
    }
  }
  
  delay(10);
}

void updateLedRing() {
  if (cameraActive) {
    // Камера включена - зажигаем кольцо БЕЛЫМ цветом
    for(int i = 0; i < LED_COUNT; i++) {
      ledRing.setPixelColor(i, ledRing.Color(255, 255, 255)); // Белый (R=255, G=255, B=255)
    }
  } else {
    // Камера выключена - выключаем все светодиоды
    for(int i = 0; i < LED_COUNT; i++) {
      ledRing.setPixelColor(i, ledRing.Color(0, 0, 0)); // Выключено (R=0, G=0, B=0)
    }
  }
  ledRing.show(); // Применяем изменения
}
