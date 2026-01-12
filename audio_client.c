#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <alsa/asoundlib.h>

#define SERVER_IP ""
#define SERVER_PORT 5000
#define SECRET_KEY ""
#define SAMPLE_RATE 16000

int main() {
    int sockfd;
    struct sockaddr_in server_addr;
    snd_pcm_t *capture_handle;
    short buf[1024];
    int err;
    char auth_msg[256];

    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Erro ao criar socket");
        return 1;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

    sprintf(auth_msg, "AUTH:%s", SECRET_KEY);
    printf("Autenticando com o servidor...\n");
    for(int i=0; i<5; i++) {
        sendto(sockfd, auth_msg, strlen(auth_msg), 0, 
               (struct sockaddr*)&server_addr, sizeof(server_addr));
        usleep(50000);
    }

    const char *mic_device = "plughw:0,0";
    
    if ((err = snd_pcm_open(&capture_handle, mic_device, SND_PCM_STREAM_CAPTURE, 0)) < 0) {
        printf("plughw:1,0 falhou, tentando 'default'...\n");
        mic_device = "default";
        if ((err = snd_pcm_open(&capture_handle, mic_device, SND_PCM_STREAM_CAPTURE, 0)) < 0) {
            fprintf(stderr, "Erro fatal: Não encontrado microfone: %s\n", snd_strerror(err));
            return 1;
        }
    }

    if ((err = snd_pcm_set_params(capture_handle,
                                  SND_PCM_FORMAT_S16_LE,
                                  SND_PCM_ACCESS_RW_INTERLEAVED,
                                  1,
                                  SAMPLE_RATE,
                                  1,
                                  100000)) < 0) {
        fprintf(stderr, "Erro parâmetros mic: %s\n", snd_strerror(err));
        return 1;
    }

    printf("Microfone (%s) -> Enviando para %s:%d\n", mic_device, SERVER_IP, SERVER_PORT);

    while(1) {
        err = snd_pcm_readi(capture_handle, buf, 1024);
        
        if (err < 0) {
            snd_pcm_recover(capture_handle, err, 0);
            continue;
        }

        sendto(sockfd, buf, 1024 * sizeof(short), 0, 
               (struct sockaddr*)&server_addr, sizeof(server_addr));
    }

    snd_pcm_close(capture_handle);
    close(sockfd);
    return 0;
}