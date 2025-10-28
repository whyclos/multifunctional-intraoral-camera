/*
 * Arduino Camera Controller
 * Не реализована подсветка светодиодного кольца, только управление кнопкой
 */

const int BUTTON_PIN = 3;

// Переменные для обработки кнопки
int lastButtonState = HIGH;
unsigned long pressStartTime = 0;
const unsigned long DEBOUNCE_DELAY = 50;
const unsigned long LONG_PRESS_TIME = 1000; // 1 секунда для длинного нажатия

bool longPressSent = false;

void setup() {
  Serial.begin(9600);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
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
          // Короткое нажатие (отпущено до истечения времени длинного нажатия)
          Serial.println("SHORT_PRESS");
        }
        // Для длинных нажатий сообщение уже отправлено в процессе удержания
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
