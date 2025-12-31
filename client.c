#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <alsa/asoundlib.h>

#define SERVER_IP "192.168.3.9"
#define SERVER_PORT 5000
#define SAMPLE_RATE 16000
#define CHANNELS 1
#define BUFFER_SIZE 1024

int main() {
    int sockfd;
    struct sockaddr_in server_addr;
    snd_pcm_t *capture_handle;
    short buf[BUFFER_SIZE];
    int err;
    
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("Erro ao criar socket");
        return 1;
    }
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);
    
    err = snd_pcm_open(&capture_handle, "plughw:2,0", SND_PCM_STREAM_CAPTURE, 0);
    if (err < 0) {
        fprintf(stderr, "Erro ao abrir dispositivo de áudio: %s\n", snd_strerror(err));
        return 1;
    }
    
    err = snd_pcm_set_params(capture_handle, SND_PCM_FORMAT_S16_LE, 
                             SND_PCM_ACCESS_RW_INTERLEAVED, 
                             CHANNELS, SAMPLE_RATE, 1, 100000);
    if (err < 0) {
        fprintf(stderr, "Erro ao configurar áudio: %s\n", snd_strerror(err));
        return 1;
    }
    
    printf("Capturando de USB Microphone...\n");
    printf("Enviando para %s:%d\n", SERVER_IP, SERVER_PORT);
    
    while(1) {
        err = snd_pcm_readi(capture_handle, buf, BUFFER_SIZE);
        if (err < 0) {
            snd_pcm_recover(capture_handle, err, 0);
            continue;
        }
        sendto(sockfd, buf, BUFFER_SIZE * sizeof(short), 0, 
               (struct sockaddr*)&server_addr, sizeof(server_addr));
    }
    
    snd_pcm_close(capture_handle);
    close(sockfd);
    return 0;
}