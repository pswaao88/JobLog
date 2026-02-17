FROM nginx:1.27-alpine

COPY app/frontend /usr/share/nginx/html
COPY deploy/frontend-nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
