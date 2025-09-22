FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY production.conf /etc/nginx/conf.d/production.conf

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"] 