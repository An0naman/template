#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include "esp_adc/adc_oneshot.h"
#include <ArduinoJson.h>

static const char *TAG = "SENSOR_FW";

#define LED_GPIO GPIO_NUM_15
// On FireBeetle 2 ESP32-C6, A0 is GPIO 0.
// ESP32-C6 ADC1 Channel 0 is GPIO 0.

extern "C" void app_main(void)
{
    ESP_LOGI(TAG, "Starting Sensor Firmware (ESP-IDF + ArduinoJson)");

    // GPIO Init
    gpio_config_t io_conf = {};
    io_conf.pin_bit_mask = (1ULL << LED_GPIO);
    io_conf.mode = GPIO_MODE_OUTPUT;
    io_conf.pull_up_en = GPIO_PULLUP_DISABLE;
    io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
    io_conf.intr_type = GPIO_INTR_DISABLE;
    gpio_config(&io_conf);

    // ADC Init (Simplified)
    adc_oneshot_unit_handle_t adc1_handle;
    adc_oneshot_unit_init_cfg_t init_config1 = {
        .unit_id = ADC_UNIT_1,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&init_config1, &adc1_handle));

    adc_oneshot_chan_cfg_t config = {
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_0, &config));

    // JSON Example
    JsonDocument doc;
    doc["sensor"] = "battery";
    doc["value"] = 0;

    while (1) {
        // Blink
        gpio_set_level(LED_GPIO, 1);
        vTaskDelay(pdMS_TO_TICKS(100));
        gpio_set_level(LED_GPIO, 0);
        vTaskDelay(pdMS_TO_TICKS(900));

        // Read Battery
        int adc_raw;
        ESP_ERROR_CHECK(adc_oneshot_read(adc1_handle, ADC_CHANNEL_0, &adc_raw));
        
        // Convert to voltage (approximate)
        // 12-bit ADC (0-4095) -> 0-3.3V (atten 11db/12db) -> Divider x2
        float voltage = (adc_raw / 4095.0) * 3.3 * 2;

        doc["value"] = voltage;
        
        char buffer[128];
        serializeJson(doc, buffer);
        ESP_LOGI(TAG, "Telemetry: %s", buffer);
    }
}
